import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_field_operator, require_super_admin
from app.core.http import raise_bad_request, raise_not_found
from app.models.user import User
from app.repositories.visit_repository import VisitRepository
from app.schemas.visit_form import (
    FormQuestionCreate,
    FormQuestionOptionCreate,
    FormQuestionOptionUpdate,
    FormQuestionOut,
    FormQuestionUpdate,
    FormTemplateCreate,
    FormTemplateOut,
    FormTemplateSummary,
    FormTemplateUpdate,
    VisitFormContextOut,
)
from app.services.visit_form_service import VisitFormService, VisitFormServiceError

router = APIRouter(prefix="/api/v1/visit-forms", tags=["visit-forms"])


@router.get("/active", response_model=FormTemplateOut)
async def get_active_visit_form(
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = VisitFormService(db)
    try:
        return await service.get_active_template()
    except VisitFormServiceError as e:
        raise_bad_request(str(e))


@router.get("/templates", response_model=list[FormTemplateSummary])
async def list_visit_form_templates(
    _current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = VisitFormService(db)
    return await service.list_templates()


@router.post("/templates", response_model=FormTemplateOut, status_code=status.HTTP_201_CREATED)
async def create_visit_form_template(
    payload: FormTemplateCreate,
    _current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = VisitFormService(db)
    try:
        template = await service.create_template(payload)
        await db.commit()
        return template
    except VisitFormServiceError as e:
        raise_bad_request(str(e))


@router.get("/templates/{template_id}", response_model=FormTemplateOut)
async def get_visit_form_template(
    template_id: uuid.UUID,
    _current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = VisitFormService(db)
    try:
        return await service.get_template(template_id)
    except VisitFormServiceError as e:
        raise_not_found(str(e))


@router.patch("/templates/{template_id}", response_model=FormTemplateOut)
async def update_visit_form_template(
    template_id: uuid.UUID,
    payload: FormTemplateUpdate,
    _current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = VisitFormService(db)
    try:
        template = await service.update_template(template_id, payload)
        await db.commit()
        return template
    except VisitFormServiceError as e:
        raise_bad_request(str(e))


@router.post("/templates/{template_id}/activate", response_model=FormTemplateOut)
async def activate_visit_form_template(
    template_id: uuid.UUID,
    _current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = VisitFormService(db)
    try:
        template = await service.activate_template(template_id)
        await db.commit()
        return template
    except VisitFormServiceError as e:
        raise_bad_request(str(e))


@router.post(
    "/templates/{template_id}/questions",
    response_model=FormQuestionOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_visit_form_question(
    template_id: uuid.UUID,
    payload: FormQuestionCreate,
    _current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = VisitFormService(db)
    try:
        question = await service.add_question(template_id, payload)
        await db.commit()
        return question
    except VisitFormServiceError as e:
        raise_bad_request(str(e))


@router.patch("/questions/{question_id}", response_model=FormQuestionOut)
async def update_visit_form_question(
    question_id: uuid.UUID,
    payload: FormQuestionUpdate,
    _current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = VisitFormService(db)
    try:
        question = await service.update_question(question_id, payload)
        await db.commit()
        return question
    except VisitFormServiceError as e:
        raise_bad_request(str(e))


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_visit_form_question(
    question_id: uuid.UUID,
    _current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = VisitFormService(db)
    try:
        await service.delete_question(question_id)
        await db.commit()
    except VisitFormServiceError as e:
        raise_bad_request(str(e))


@router.post(
    "/questions/{question_id}/options",
    response_model=FormQuestionOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_visit_form_option(
    question_id: uuid.UUID,
    payload: FormQuestionOptionCreate,
    _current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = VisitFormService(db)
    try:
        question = await service.add_option(question_id, payload)
        await db.commit()
        return question
    except VisitFormServiceError as e:
        raise_bad_request(str(e))


@router.patch("/options/{option_id}", response_model=FormQuestionOut)
async def update_visit_form_option(
    option_id: uuid.UUID,
    payload: FormQuestionOptionUpdate,
    _current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = VisitFormService(db)
    try:
        question = await service.update_option(option_id, payload)
        await db.commit()
        return question
    except VisitFormServiceError as e:
        raise_bad_request(str(e))


@router.delete("/options/{option_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_visit_form_option(
    option_id: uuid.UUID,
    _current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = VisitFormService(db)
    try:
        await service.delete_option(option_id)
        await db.commit()
    except VisitFormServiceError as e:
        raise_bad_request(str(e))


@router.get("/visits/{visit_id}/context", response_model=VisitFormContextOut)
async def get_visit_form_context(
    visit_id: uuid.UUID,
    current_user: User = Depends(require_field_operator),
    db: AsyncSession = Depends(get_db),
):
    visit_repo = VisitRepository(db)
    visit = await visit_repo.get_by_id(visit_id)
    if visit is None:
        raise_not_found("Visit not found")
    if visit.executive_id != current_user.id:
        raise_bad_request("You do not have access to this visit")

    service = VisitFormService(db)
    try:
        return await service.build_visit_context(visit)
    except VisitFormServiceError as e:
        raise_bad_request(str(e))
