from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.db.session import get_db
from app.schemas.teacher import TeacherCreate, TeacherRead
from app.services.teacher_service import TeacherService

router = APIRouter(prefix="/teachers", tags=["teachers"])


@router.get("/", response_model=list[TeacherRead])
def list_teachers(
    _: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[TeacherRead]:
    service = TeacherService(db)
    return service.list_teachers()


@router.get("/{teacher_id}", response_model=TeacherRead)
def get_teacher(
    teacher_id: int,
    _: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> TeacherRead:
    service = TeacherService(db)
    return service.get_teacher(teacher_id)


@router.post("/", response_model=TeacherRead, status_code=status.HTTP_201_CREATED)
def create_teacher(
    data: TeacherCreate,
    _: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> TeacherRead:
    service = TeacherService(db)
    return service.create_teacher(data)


@router.put("/{teacher_id}", response_model=TeacherRead)
def update_teacher(
    teacher_id: int,
    data: TeacherCreate,
    _: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> TeacherRead:
    service = TeacherService(db)
    return service.update_teacher(teacher_id, data)


@router.delete("/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_teacher(
    teacher_id: int,
    _: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Response:
    service = TeacherService(db)
    service.delete_teacher(teacher_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
