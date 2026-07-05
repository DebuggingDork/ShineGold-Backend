import csv
import io
import uuid
from dataclasses import dataclass

from openpyxl import Workbook, load_workbook
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import BulkImportOut, BulkImportRowError, BulkImportedUser

IMPORT_COLUMNS = ("employee_id", "name", "mobile_number")
TEMPLATE_HEADERS = ("employee_id", "name", "mobile_number")
TEMPLATE_SAMPLE = ("EMP1001", "Ravi Kumar", "9876543210")


class BulkImportError(Exception):
    pass


@dataclass
class ImportRow:
    row_number: int
    employee_id: str
    name: str
    mobile_number: str | None = None


class BulkImportService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    @staticmethod
    def build_template_bytes() -> bytes:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Executives"
        sheet.append(list(TEMPLATE_HEADERS))
        sheet.append(list(TEMPLATE_SAMPLE))
        buffer = io.BytesIO()
        workbook.save(buffer)
        return buffer.getvalue()

    @staticmethod
    def parse_upload(content: bytes, filename: str) -> list[ImportRow]:
        lowered = filename.lower()
        if lowered.endswith(".csv"):
            return BulkImportService._parse_csv(content)
        if lowered.endswith((".xlsx", ".xlsm")):
            return BulkImportService._parse_xlsx(content)
        raise BulkImportError("Unsupported file type. Upload a .xlsx or .csv file.")

    @staticmethod
    def _normalize_header(value: object | None) -> str:
        if value is None:
            return ""
        return str(value).strip().lower().replace(" ", "_")

    @classmethod
    def _parse_xlsx(cls, content: bytes) -> list[ImportRow]:
        workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        sheet = workbook.active
        rows = sheet.iter_rows(values_only=True)
        try:
            header_row = next(rows)
        except StopIteration as e:
            raise BulkImportError("The uploaded file is empty.") from e

        headers = [cls._normalize_header(cell) for cell in header_row]
        column_index = {header: idx for idx, header in enumerate(headers) if header}

        missing = [col for col in ("employee_id", "name") if col not in column_index]
        if missing:
            raise BulkImportError(
                f"Missing required columns: {', '.join(missing)}. "
                f"Expected headers: employee_id, name, mobile_number"
            )

        parsed: list[ImportRow] = []
        for offset, row in enumerate(rows, start=2):
            if row is None or not any(row):
                continue

            employee_id = str(row[column_index["employee_id"]] or "").strip()
            name = str(row[column_index["name"]] or "").strip()
            mobile_number = None
            if "mobile_number" in column_index:
                raw_mobile = row[column_index["mobile_number"]]
                mobile_number = str(raw_mobile).strip() if raw_mobile not in (None, "") else None

            if not employee_id and not name:
                continue
            parsed.append(
                ImportRow(
                    row_number=offset,
                    employee_id=employee_id,
                    name=name,
                    mobile_number=mobile_number,
                )
            )
        workbook.close()
        return parsed

    @staticmethod
    def _parse_csv(content: bytes) -> list[ImportRow]:
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames:
            raise BulkImportError("The uploaded CSV file is empty.")

        headers = {
            BulkImportService._normalize_header(name): name
            for name in reader.fieldnames
            if name
        }
        missing = [col for col in ("employee_id", "name") if col not in headers]
        if missing:
            raise BulkImportError(
                f"Missing required columns: {', '.join(missing)}. "
                f"Expected headers: employee_id, name, mobile_number"
            )

        parsed: list[ImportRow] = []
        for offset, row in enumerate(reader, start=2):
            employee_id = (row.get(headers["employee_id"]) or "").strip()
            name = (row.get(headers["name"]) or "").strip()
            mobile_number = None
            if "mobile_number" in headers:
                raw_mobile = (row.get(headers["mobile_number"]) or "").strip()
                mobile_number = raw_mobile or None

            if not employee_id and not name:
                continue
            parsed.append(
                ImportRow(
                    row_number=offset,
                    employee_id=employee_id,
                    name=name,
                    mobile_number=mobile_number,
                )
            )
        return parsed

    async def import_executives(
        self,
        rows: list[ImportRow],
        default_password: str,
    ) -> BulkImportOut:
        if not rows:
            raise BulkImportError("No executive rows found in the uploaded file.")

        created_users: list[BulkImportedUser] = []
        errors: list[BulkImportRowError] = []
        skipped = 0
        seen_employee_ids: set[str] = set()

        for row in rows:
            if not row.employee_id or not row.name:
                skipped += 1
                errors.append(
                    BulkImportRowError(
                        row=row.row_number,
                        employee_id=row.employee_id or None,
                        reason="employee_id and name are required",
                    )
                )
                continue

            if row.employee_id in seen_employee_ids:
                skipped += 1
                errors.append(
                    BulkImportRowError(
                        row=row.row_number,
                        employee_id=row.employee_id,
                        reason="Duplicate employee_id in file",
                    )
                )
                continue
            seen_employee_ids.add(row.employee_id)

            existing = await self.user_repo.get_by_employee_id(row.employee_id)
            if existing is not None:
                skipped += 1
                errors.append(
                    BulkImportRowError(
                        row=row.row_number,
                        employee_id=row.employee_id,
                        reason="Employee ID already exists",
                    )
                )
                continue

            user = User(
                employee_id=row.employee_id,
                name=row.name,
                password_hash=hash_password(default_password),
                role=UserRole.EXECUTIVE,
                mobile_number=row.mobile_number,
            )
            created = await self.user_repo.create(user)
            created_users.append(
                BulkImportedUser(
                    id=created.id,
                    employee_id=created.employee_id,
                    name=created.name,
                    default_password=default_password,
                )
            )

        return BulkImportOut(
            created=len(created_users),
            skipped=skipped,
            errors=errors,
            users=created_users,
        )
