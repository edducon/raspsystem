from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user
from app.db.session import get_db
from app.schemas.teacher_directory import TeacherDirectoryRead
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
