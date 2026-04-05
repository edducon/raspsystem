from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_active_user,
    get_optional_current_user,
    require_admin,
    require_scheduler_roles,
)
from app.db.session import get_db
from app.models import User
from app.schemas.retake_admin import (
    PastSemesterImportRequest,
    PastSemesterImportResponse,
    PastSemesterStatusResponse,
    RetakeResetResponse,
)
from app.schemas.retake import (
    GroupHistoryEntryRead,
    GroupRetakeRead,
    RetakeFormContextRead,
    RetakeFormContextRequest,
    MergedDayScheduleRequest,
    MergedDaySlotRead,
    RetakeCreateRequest,
    RetakeRead,
    TeacherRetakeRead,
)
from app.services.retake_admin_service import RetakeAdminService
from app.services.retake_service import RetakeService

router = APIRouter(prefix="/retakes", tags=["retakes"])


@router.get("/", response_model=list[RetakeRead])
def list_retakes(
        current_user: User | None = Depends(get_optional_current_user),
        db: Session = Depends(get_db),
) -> list[RetakeRead]:
    return RetakeService(db).list_retakes(viewer=current_user)


@router.get("/mine", response_model=list[TeacherRetakeRead])
def list_my_retakes(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db),
) -> list[TeacherRetakeRead]:
    return RetakeService(db).list_my_retakes(user=current_user)


@router.get("/group/{group_uuid}", response_model=list[GroupRetakeRead])
def list_group_retakes(
        group_uuid: str,
        current_user: User = Depends(require_scheduler_roles),
        db: Session = Depends(get_db),
) -> list[GroupRetakeRead]:
    return RetakeService(db).list_group_retakes(group_uuid=group_uuid, viewer=current_user)


@router.get("/history/group/{group_name}", response_model=list[GroupHistoryEntryRead])
def get_group_history(
        group_name: str,
        _: User = Depends(require_scheduler_roles),
        db: Session = Depends(get_db),
) -> list[GroupHistoryEntryRead]:
    return RetakeService(db).list_group_history(group_name=group_name)


@router.post("/form-context", response_model=RetakeFormContextRead)
def get_retake_form_context(
        payload: RetakeFormContextRequest,
        current_user: User = Depends(require_scheduler_roles),
        db: Session = Depends(get_db),
) -> RetakeFormContextRead:
    return RetakeService(db).get_form_context(payload=payload, user=current_user)


@router.post("/merged-day", response_model=dict[str, MergedDaySlotRead | None])
def get_merged_day_schedule(
        payload: MergedDayScheduleRequest,
        _: User = Depends(require_scheduler_roles),
        db: Session = Depends(get_db),
) -> dict[str, MergedDaySlotRead | None]:
    return RetakeService(db).get_merged_day_schedule(payload)


@router.post("/", response_model=RetakeRead, status_code=status.HTTP_201_CREATED)
def create_retake(
        payload: RetakeCreateRequest,
        current_user: User = Depends(require_scheduler_roles),
        db: Session = Depends(get_db),
) -> RetakeRead:
    return RetakeService(db).create_retake(data=payload, user=current_user)


@router.post("/admin/past-semester/import", response_model=PastSemesterImportResponse)
def import_past_semester(
        payload: PastSemesterImportRequest | None = None,
        _: User = Depends(require_admin),
        db: Session = Depends(get_db),
) -> PastSemesterImportResponse:
    return RetakeAdminService(db).import_past_semester(source_path=payload.source_path if payload else None)


@router.get("/admin/past-semester/status", response_model=PastSemesterStatusResponse)
def get_past_semester_status(
        _: User = Depends(require_admin),
        db: Session = Depends(get_db),
) -> PastSemesterStatusResponse:
    return RetakeAdminService(db).get_past_semester_status()


@router.post("/admin/past-semester/import-json", response_model=PastSemesterImportResponse)
def import_past_semester_json(
        payload: dict,
        _: User = Depends(require_admin),
        db: Session = Depends(get_db),
) -> PastSemesterImportResponse:
    return RetakeAdminService(db).import_past_semester_json(payload)


@router.post("/admin/past-semester/import-current", response_model=PastSemesterImportResponse)
def import_current_semester_as_past(
        _: User = Depends(require_admin),
        db: Session = Depends(get_db),
) -> PastSemesterImportResponse:
    return RetakeAdminService(db).import_current_semester_as_past()


@router.post("/admin/sync-teachers")
def sync_teachers_from_api(
        _: User = Depends(require_admin),
        db: Session = Depends(get_db),
) -> dict:
    from app.services.teacher_sync_service import TeacherSyncService
    return TeacherSyncService(db).sync_from_api()


@router.post("/admin/reset", response_model=RetakeResetResponse)
def reset_retakes(
        _: User = Depends(require_admin),
        db: Session = Depends(get_db),
) -> RetakeResetResponse:
    return RetakeAdminService(db).reset_retakes()


@router.delete("/{retake_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_retake(
        retake_id: str,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db),
) -> Response:
    RetakeService(db).delete_retake(retake_id=retake_id, user=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
