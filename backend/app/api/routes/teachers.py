from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.db.session import get_db
from app.schemas.teacher import TeacherCreate, TeacherRead
from app.services.audit_service import AuditService
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
    request: Request,
    current_admin: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> TeacherRead:
    service = TeacherService(db)
    teacher = service.create_teacher(data)
    AuditService(db).record(
        action="admin.teacher.create",
        actor=current_admin,
        request=request,
        target_type="teacher",
        target_id=str(teacher.id),
        details={"full_name": teacher.full_name},
    )
    return teacher


@router.put("/{teacher_id}", response_model=TeacherRead)
def update_teacher(
    teacher_id: int,
    data: TeacherCreate,
    request: Request,
    current_admin: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> TeacherRead:
    service = TeacherService(db)
    teacher = service.update_teacher(teacher_id, data)
    AuditService(db).record(
        action="admin.teacher.update",
        actor=current_admin,
        request=request,
        target_type="teacher",
        target_id=str(teacher.id),
        details={"full_name": teacher.full_name},
    )
    return teacher


@router.delete("/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_teacher(
    teacher_id: int,
    request: Request,
    current_admin: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Response:
    service = TeacherService(db)
    teacher = service.get_teacher(teacher_id)
    service.delete_teacher(teacher_id)
    AuditService(db).record(
        action="admin.teacher.delete",
        actor=current_admin,
        request=request,
        target_type="teacher",
        target_id=str(teacher_id),
        details={"full_name": teacher.full_name},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
