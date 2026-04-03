from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.department import DepartmentCreate, DepartmentRead
from app.services.department_service import DepartmentService

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("/", response_model=list[DepartmentRead])
def list_departments(db: Session = Depends(get_db)) -> list[DepartmentRead]:
    service = DepartmentService(db)
    return service.list_departments()


@router.get("/{department_id}", response_model=DepartmentRead)
def get_department(department_id: int, db: Session = Depends(get_db)) -> DepartmentRead:
    service = DepartmentService(db)
    return service.get_department(department_id)


@router.post("/", response_model=DepartmentRead, status_code=status.HTTP_201_CREATED)
def create_department(data: DepartmentCreate, db: Session = Depends(get_db)) -> DepartmentRead:
    service = DepartmentService(db)
    return service.create_department(data)


@router.put("/{department_id}", response_model=DepartmentRead)
def update_department(
        department_id: int,
        data: DepartmentCreate,
        db: Session = Depends(get_db),
) -> DepartmentRead:
    service = DepartmentService(db)
    return service.update_department(department_id, data)


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(department_id: int, db: Session = Depends(get_db)) -> Response:
    service = DepartmentService(db)
    service.delete_department(department_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)