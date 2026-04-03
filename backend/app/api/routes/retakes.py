from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_active_user,
    get_optional_current_user,
    require_scheduler_roles,
)
from app.db.session import get_db
from app.models import User
from app.schemas.retake import (
    GroupHistoryEntryRead,
    GroupRetakeRead,
    MergedDayScheduleRequest,
    MergedDaySlotRead,
    RetakeCreateRequest,
    RetakeRead,
    TeacherRetakeRead,
)
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


@router.delete("/{retake_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_retake(
    retake_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Response:
    RetakeService(db).delete_retake(retake_id=retake_id, user=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
