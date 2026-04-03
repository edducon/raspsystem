from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user
from app.db.session import get_db
from app.schemas.schedule_data import ScheduleDictionariesRead, TeacherScheduleRead
from app.services.schedule_data_service import ScheduleDataService

router = APIRouter(prefix="/schedule-data", tags=["schedule-data"])


@router.get("/dictionaries", response_model=ScheduleDictionariesRead)
def get_dictionaries(db: Session = Depends(get_db)) -> ScheduleDictionariesRead:
    return ScheduleDataService(db).get_dictionaries()


@router.get("/teacher/{teacher_uuid}", response_model=TeacherScheduleRead)
def get_teacher_schedule(
    teacher_uuid: str,
    _: object = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> TeacherScheduleRead:
    return ScheduleDataService(db).get_teacher_schedule(teacher_uuid)
