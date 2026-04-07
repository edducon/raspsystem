from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.db.session import get_db
from app.schemas.audit_log import AuditLogListResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


@router.get("/", response_model=AuditLogListResponse)
def list_audit_logs(
    _: object = Depends(require_admin),
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    action: str | None = Query(default=None),
    status: str | None = Query(default=None),
    actor_user_id: int | None = Query(default=None, alias="actorUserId", ge=1),
    q: str | None = Query(default=None, min_length=1, max_length=255),
) -> AuditLogListResponse:
    items, total = AuditService(db).list_logs(
        limit=limit,
        offset=offset,
        action=action,
        status=status,
        actor_user_id=actor_user_id,
        query=q,
    )
    return AuditLogListResponse(items=items, total=total, limit=limit, offset=offset)
