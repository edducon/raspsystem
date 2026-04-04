from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user, require_admin
from app.db.session import get_db
from app.schemas.teacher_directory import TeacherDirectoryCreate, TeacherDirectoryRead, TeacherDirectoryUpdate
from app.services.teacher_directory_service import TeacherDirectoryService

router = APIRouter(prefix="/teacher-directory", tags=["teacher-directory"])


@router.get("/", response_model=list[TeacherDirectoryRead])
def list_teacher_directory(
    _: object = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[TeacherDirectoryRead]:
    return TeacherDirectoryService(db).list_teachers()


@router.get("/{teacher_uuid}", response_model=TeacherDirectoryRead)
def get_teacher_directory_entry(
    teacher_uuid: str,
    _: object = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> TeacherDirectoryRead:
    return TeacherDirectoryService(db).get_teacher(teacher_uuid)


@router.post("/", response_model=TeacherDirectoryRead, status_code=status.HTTP_201_CREATED)
def create_teacher_directory_entry(
    data: TeacherDirectoryCreate,
    _: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> TeacherDirectoryRead:
    return TeacherDirectoryService(db).create_teacher(data)


@router.put("/{teacher_uuid}", response_model=TeacherDirectoryRead)
def update_teacher_directory_entry(
    teacher_uuid: str,
    data: TeacherDirectoryUpdate,
    _: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> TeacherDirectoryRead:
    return TeacherDirectoryService(db).update_teacher(teacher_uuid, data)


@router.delete("/{teacher_uuid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_teacher_directory_entry(
    teacher_uuid: str,
    _: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Response:
    TeacherDirectoryService(db).delete_teacher(teacher_uuid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/sync", response_model=dict)
def sync_teacher_directory(
        _: object = Depends(require_admin),
        db: Session = Depends(get_db),
) -> dict:
    return TeacherDirectoryService(db).sync_teachers()
