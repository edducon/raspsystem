from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.departments import router as departments_router
from app.api.routes.health import router as health_router
from app.api.routes.positions import router as positions_router
from app.api.routes.schedule_snapshots import router as schedule_snapshots_router
from app.api.routes.teachers import router as teachers_router
from app.api.routes.users import router as users_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(health_router)
api_router.include_router(departments_router)
api_router.include_router(positions_router)
api_router.include_router(schedule_snapshots_router)
api_router.include_router(teachers_router)
api_router.include_router(users_router)
