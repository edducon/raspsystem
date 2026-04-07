from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime
from decimal import Decimal

from fastapi import Request
from sqlalchemy import Text, cast, func, or_, select
from sqlalchemy.orm import Session, aliased

from app.models import AuditLog, User


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record(
        self,
        *,
        action: str,
        actor: User | None = None,
        request: Request | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        status: str = "SUCCESS",
        details: Mapping[str, object] | None = None,
        commit: bool = True,
    ) -> AuditLog:
        log = AuditLog(
            actor_user_id=actor.id if actor else None,
            action=action,
            target_type=target_type,
            target_id=target_id,
            status=status,
            ip_address=self._client_ip(request) if request else None,
            user_agent=self._user_agent(request) if request else None,
            details=self._make_json_safe(dict(details)) if details else None,
        )
        self.db.add(log)
        if commit:
            self.db.commit()
            self.db.refresh(log)
        return log

    def list_logs(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        action: str | None = None,
        status: str | None = None,
        actor_user_id: int | None = None,
        query: str | None = None,
    ) -> tuple[list[AuditLog], int]:
        normalized_limit = max(1, min(limit, 500))
        normalized_offset = max(0, offset)
        actor = aliased(User)
        conditions = []

        normalized_action = action.strip() if action else None
        normalized_status = status.strip().upper() if status else None
        normalized_query = query.strip() if query else None

        if normalized_action:
            conditions.append(AuditLog.action == normalized_action)
        if normalized_status:
            conditions.append(AuditLog.status == normalized_status)
        if actor_user_id is not None:
            conditions.append(AuditLog.actor_user_id == actor_user_id)
        if normalized_query:
            search_pattern = f"%{normalized_query}%"
            conditions.append(
                or_(
                    AuditLog.action.ilike(search_pattern),
                    func.coalesce(AuditLog.target_type, "").ilike(search_pattern),
                    func.coalesce(AuditLog.target_id, "").ilike(search_pattern),
                    AuditLog.status.ilike(search_pattern),
                    func.coalesce(AuditLog.ip_address, "").ilike(search_pattern),
                    func.coalesce(AuditLog.user_agent, "").ilike(search_pattern),
                    func.coalesce(actor.username, "").ilike(search_pattern),
                    func.coalesce(actor.full_name, "").ilike(search_pattern),
                    cast(AuditLog.details, Text).ilike(search_pattern),
                )
            )

        statement = select(AuditLog).outerjoin(actor, AuditLog.actor_user_id == actor.id)
        count_statement = select(func.count()).select_from(AuditLog).outerjoin(actor, AuditLog.actor_user_id == actor.id)

        if conditions:
            statement = statement.where(*conditions)
            count_statement = count_statement.where(*conditions)

        total = int(self.db.scalar(count_statement) or 0)
        logs = list(
            self.db.scalars(
                statement
                .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
                .offset(normalized_offset)
                .limit(normalized_limit)
            ).all()
        )
        return logs, total

    def _client_ip(self, request: Request) -> str | None:
        forwarded_for = request.headers.get("x-forwarded-for", "")
        if forwarded_for:
            return forwarded_for.split(",", 1)[0].strip() or None
        return request.client.host if request.client else None

    def _user_agent(self, request: Request) -> str | None:
        user_agent = request.headers.get("user-agent", "").strip()
        return user_agent or None

    def _make_json_safe(self, value: object) -> object:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, Mapping):
            return {str(key): self._make_json_safe(nested) for key, nested in value.items()}
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return [self._make_json_safe(item) for item in value]
        return str(value)
