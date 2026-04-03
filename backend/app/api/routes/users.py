from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.models import User
from app.db.session import get_db
from app.schemas.user import UserCreate, UserRead, UserUpdate
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
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserRead:
    service = UserService(db)
    return service.create_user(data)


@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    data: UserUpdate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserRead:
    service = UserService(db)
    return service.update_user(user_id, data, actor=current_admin)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Response:
    service = UserService(db)
    service.delete_user(user_id, actor=current_admin)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
