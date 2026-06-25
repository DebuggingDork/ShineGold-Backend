import enum


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    EXECUTIVE = "executive"


class FarmStatus(str, enum.Enum):
    PENDING_VISIT = "pending_visit"
    VISITED = "visited"
    HARVESTED = "harvested"


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class VisitStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PasswordResetStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"