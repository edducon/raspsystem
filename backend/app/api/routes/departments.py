from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user, require_admin
from app.db.session import get_db
from app.schemas.department import DepartmentCreate, DepartmentRead
from app.services.audit_service import AuditService
from app.services.department_service import DepartmentService

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("/", response_model=list[DepartmentRead])
def list_departments(
    _: object = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[DepartmentRead]:
    service = DepartmentService(db)
    return service.list_departments()


@router.get("/{department_id}", response_model=DepartmentRead)
def get_department(
    department_id: int,
    _: object = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DepartmentRead:
    service = DepartmentService(db)
    return service.get_department(department_id)


@router.post("/", response_model=DepartmentRead, status_code=status.HTTP_201_CREATED)
def create_department(
    data: DepartmentCreate,
    request: Request,
    current_admin: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> DepartmentRead:
    service = DepartmentService(db)
    department = service.create_department(data)
    AuditService(db).record(
        action="admin.department.create",
        actor=current_admin,
        request=request,
        target_type="department",
        target_id=str(department.id),
        details={"name": department.name, "short_name": department.short_name},
    )
    return department


@router.put("/{department_id}", response_model=DepartmentRead)
def update_department(
    department_id: int,
    data: DepartmentCreate,
    request: Request,
    current_admin: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> DepartmentRead:
    service = DepartmentService(db)
    department = service.update_department(department_id, data)
    AuditService(db).record(
        action="admin.department.update",
        actor=current_admin,
        request=request,
        target_type="department",
        target_id=str(department.id),
        details={"name": department.name, "short_name": department.short_name},
    )
    return department


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(
    department_id: int,
    request: Request,
    current_admin: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Response:
    service = DepartmentService(db)
    department = service.get_department(department_id)
    service.delete_department(department_id)
    AuditService(db).record(
        action="admin.department.delete",
        actor=current_admin,
        request=request,
        target_type="department",
        target_id=str(department_id),
        details={"name": department.name, "short_name": department.short_name},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
