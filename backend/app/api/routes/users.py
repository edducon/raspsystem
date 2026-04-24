from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.models import User
from app.db.session import get_db
from app.schemas.user import UserCreate, UserRead, UserSchedulePermissionsUpdate, UserUpdate
from app.services.audit_service import AuditService
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserRead])
def list_users(
    _: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[UserRead]:
    service = UserService(db)
    return service.list_users()


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    _: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserRead:
    service = UserService(db)
    return service.get_user(user_id)


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    request: Request,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserRead:
    service = UserService(db)
    created_user = service.create_user(data)
    AuditService(db).record(
        action="admin.user.create",
        actor=current_admin,
        request=request,
        target_type="user",
        target_id=str(created_user.id),
        details={"username": created_user.username, "role": created_user.role},
    )
    return created_user


@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    data: UserUpdate,
    request: Request,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserRead:
    service = UserService(db)
    updated_user = service.update_user(user_id, data, actor=current_admin)
    AuditService(db).record(
        action="admin.user.update",
        actor=current_admin,
        request=request,
        target_type="user",
        target_id=str(updated_user.id),
        details={"username": updated_user.username, "role": updated_user.role},
    )
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    request: Request,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Response:
    service = UserService(db)
    user = service.get_user(user_id)
    service.delete_user(user_id, actor=current_admin)
    AuditService(db).record(
        action="admin.user.delete",
        actor=current_admin,
        request=request,
        target_type="user",
        target_id=str(user_id),
        details={"username": user.username},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{user_id}/schedule-permissions", response_model=UserRead)
def update_user_schedule_permissions(
    user_id: int,
    data: UserSchedulePermissionsUpdate,
    request: Request,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserRead:
    service = UserService(db)
    updated_user = service.update_schedule_permissions(user_id, data)
    AuditService(db).record(
        action="admin.user.update_schedule_permissions",
        actor=current_admin,
        request=request,
        target_type="user",
        target_id=str(updated_user.id),
        details={
            "username": updated_user.username,
            "can_schedule_semester": updated_user.can_schedule_semester,
            "can_schedule_session": updated_user.can_schedule_session,
            "can_schedule_retakes": updated_user.can_schedule_retakes,
        },
    )
    return updated_user
