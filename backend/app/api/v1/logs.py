from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import Depends, APIRouter, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, DbSession, Pagination, require_permission
from app.models import AuditLog, User
from app.schemas.common import Page
from app.schemas.logs import AuditLogOut

router = APIRouter(prefix="/audit-logs", tags=["Bitácora"])


@router.get("", response_model=Page[AuditLogOut])
def list_audit_logs(
    user: CurrentUser,
    db: DbSession,
    page_params: Pagination,
    _: User = Depends(require_permission("logs:read")),
    action: str | None = Query(default=None, max_length=100),
    module: str | None = Query(default=None, max_length=50),
    result: str | None = Query(default=None, max_length=20),
    user_id: UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> Page[AuditLogOut]:
    page, page_size = page_params
    conditions = [AuditLog.organization_id == user.organization_id]
    if action:
        conditions.append(AuditLog.action.ilike(f"%{action}%"))
    if module:
        conditions.append(AuditLog.module == module)
    if result:
        conditions.append(AuditLog.result == result)
    if user_id:
        conditions.append(AuditLog.user_id == user_id)
    if date_from:
        conditions.append(AuditLog.created_at >= date_from)
    if date_to:
        conditions.append(AuditLog.created_at <= date_to)
    total = int(db.scalar(select(func.count()).select_from(AuditLog).where(*conditions)) or 0)
    entries = db.scalars(
        select(AuditLog)
        .where(*conditions)
        .order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    user_ids = {entry.user_id for entry in entries if entry.user_id}
    names: dict[UUID, str] = {}
    if user_ids:
        names = {
            row.id: row.full_name
            for row in db.scalars(select(User).where(User.id.in_(user_ids))).all()
        }
    return Page(
        items=[
            AuditLogOut(
                **{column.name: getattr(entry, column.name) for column in AuditLog.__table__.columns},
                user_name=names.get(entry.user_id) if entry.user_id else None,
            )
            for entry in entries
        ],
        total=total,
        page=page,
        page_size=page_size,
    )
