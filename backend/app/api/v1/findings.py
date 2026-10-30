from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import Depends, APIRouter, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.deps import CurrentUser, DbSession, Pagination, require_permission
from app.enums import (
    CheckStatus,
    FindingStatus,
    RecommendationSource,
    RecommendationStatus,
    Severity,
)
from app.models import (
    CisControl,
    Finding,
    FindingEvent,
    HardeningCheck,
    RemediationRecommendation,
    RemediationReview,
    Server,
    User,
)
from app.schemas.common import Page
from app.schemas.findings import (
    FindingDetail,
    FindingEventOut,
    FindingOut,
    FindingUpdate,
    GenerateRecommendationResponse,
    RecommendationDetail,
    RecommendationOut,
    RecommendationReviewIn,
    RecommendationReviewOut,
)
from app.services.ai_service import (
    AIInvalidResponseError,
    AIUnavailableError,
    AIContext,
    build_recommendation,
)
from app.services.audit_log import record_audit

router = APIRouter(tags=["Hallazgos y recomendaciones"])

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    FindingStatus.DETECTED.value: {
        FindingStatus.IN_REVIEW.value,
        FindingStatus.CORRECTION_PLANNED.value,
        FindingStatus.RISK_ACCEPTED.value,
        FindingStatus.FALSE_POSITIVE.value,
    },
    FindingStatus.IN_REVIEW.value: {
        FindingStatus.DETECTED.value,
        FindingStatus.CORRECTION_PLANNED.value,
        FindingStatus.RISK_ACCEPTED.value,
        FindingStatus.FALSE_POSITIVE.value,
    },
    FindingStatus.CORRECTION_PLANNED.value: {
        FindingStatus.IN_REVIEW.value,
        FindingStatus.FIXED_PENDING_VALIDATION.value,
        FindingStatus.RISK_ACCEPTED.value,
    },
    FindingStatus.FIXED_PENDING_VALIDATION.value: {
        FindingStatus.CORRECTION_PLANNED.value,
        FindingStatus.RISK_ACCEPTED.value,
        FindingStatus.RESOLVED.value,
    },
    FindingStatus.RISK_ACCEPTED.value: {
        FindingStatus.DETECTED.value,
        FindingStatus.RESOLVED.value,
    },
    FindingStatus.FALSE_POSITIVE.value: {FindingStatus.DETECTED.value},
    FindingStatus.RESOLVED.value: {FindingStatus.DETECTED.value},
}


def _user_name(db: Session, user_id: UUID | None) -> str | None:
    if user_id is None:
        return None
    user = db.get(User, user_id)
    return user.full_name if user else None


def _finding_out(db: Session, finding: Finding) -> FindingOut:
    recommendations = sorted(finding.recommendations, key=lambda item: item.created_at, reverse=True)
    latest = recommendations[0] if recommendations else None
    owner = db.get(User, finding.owner_id) if finding.owner_id else None
    return FindingOut(
        **{column.name: getattr(finding, column.name) for column in Finding.__table__.columns},
        server_name=finding.server.name if finding.server else None,
        control_code=finding.control.code if finding.control else None,
        cis_reference=finding.control.cis_reference if finding.control else None,
        category=finding.control.category if finding.control else None,
        owner_name=owner.full_name if owner else None,
        recommendation_count=len(recommendations),
        latest_recommendation_id=latest.id if latest else None,
        latest_recommendation_status=latest.status if latest else None,
    )


def _get_finding(db: Session, finding_id: UUID, organization_id: UUID) -> Finding:
    finding = db.scalar(
        select(Finding)
        .where(Finding.id == finding_id, Finding.organization_id == organization_id)
        .options(
            joinedload(Finding.server),
            joinedload(Finding.control),
            selectinload(Finding.recommendations),
        )
    )
    if finding is None:
        raise HTTPException(status_code=404, detail="Hallazgo no encontrado.")
    return finding


def _latest_check(db: Session, finding: Finding) -> HardeningCheck | None:
    return db.scalar(
        select(HardeningCheck)
        .where(
            HardeningCheck.run_id == finding.last_seen_run_id,
            HardeningCheck.control_id == finding.control_id,
        )
        .options(joinedload(HardeningCheck.control))
    )


@router.get("/findings", response_model=Page[FindingOut])
def list_findings(
    user: CurrentUser,
    db: DbSession,
    page_params: Pagination,
    _: User = Depends(require_permission("findings:read")),
    finding_status: str | None = Query(default=None, alias="status", max_length=40),
    severity: str | None = Query(default=None, max_length=20),
    server_id: UUID | None = None,
    owner_id: UUID | None = None,
    search: str | None = Query(default=None, max_length=100),
    include_closed: bool = False,
) -> Page[FindingOut]:
    page, page_size = page_params
    conditions = [Finding.organization_id == user.organization_id]
    if finding_status:
        conditions.append(Finding.status == finding_status)
    elif not include_closed:
        conditions.append(
            Finding.status.notin_([FindingStatus.RESOLVED, FindingStatus.FALSE_POSITIVE])
        )
    if severity:
        conditions.append(Finding.severity == severity)
    if server_id:
        conditions.append(Finding.server_id == server_id)
    if owner_id:
        conditions.append(Finding.owner_id == owner_id)
    if search:
        pattern = f"%{search.strip()}%"
        conditions.append(
            or_(Finding.title.ilike(pattern), Finding.description.ilike(pattern))
        )
    total = int(db.scalar(select(func.count()).select_from(Finding).where(*conditions)) or 0)
    findings = db.scalars(
        select(Finding)
        .where(*conditions)
        .options(
            joinedload(Finding.server),
            joinedload(Finding.control),
            selectinload(Finding.recommendations),
        )
        .order_by(Finding.last_seen_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return Page(
        items=[_finding_out(db, item) for item in findings],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/findings/{finding_id}", response_model=FindingDetail)
def get_finding(
    finding_id: UUID,
    user: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("findings:read")),
) -> FindingDetail:
    finding = _get_finding(db, finding_id, user.organization_id)
    check = _latest_check(db, finding)
    events = db.scalars(
        select(FindingEvent)
        .where(FindingEvent.finding_id == finding.id)
        .order_by(FindingEvent.created_at.asc())
    ).all()
    base = _finding_out(db, finding)
    return FindingDetail(
        **base.model_dump(),
        evidence=check.evidence if check else {},
        observed_value=check.observed_value if check else None,
        events=[
            FindingEventOut(
                id=event.id,
                event_type=event.event_type,
                from_status=event.from_status,
                to_status=event.to_status,
                comment=event.comment,
                actor_id=event.actor_id,
                created_at=event.created_at,
                actor_name=_user_name(db, event.actor_id),
            )
            for event in events
        ],
    )


@router.patch("/findings/{finding_id}", response_model=FindingDetail)
def update_finding(
    finding_id: UUID,
    payload: FindingUpdate,
    request: Request,
    user: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("findings:manage")),
) -> FindingDetail:
    finding = _get_finding(db, finding_id, user.organization_id)
    changes: dict[str, object] = {}
    now = datetime.now(timezone.utc)
    old_status = finding.status.value

    if payload.owner_id is not None:
        owner = db.scalar(
            select(User).where(
                User.id == payload.owner_id, User.organization_id == user.organization_id
            )
        )
        if owner is None:
            raise HTTPException(status_code=422, detail="El responsable no pertenece a la organización.")
        finding.owner_id = owner.id
        changes["owner_id"] = str(owner.id)
    if payload.priority is not None:
        finding.priority = payload.priority
        changes["priority"] = payload.priority
    if payload.due_date is not None:
        finding.due_date = payload.due_date
        changes["due_date"] = payload.due_date.isoformat()
    if payload.risk_acceptance_until is not None:
        if payload.risk_acceptance_until < date.today():
            raise HTTPException(status_code=422, detail="La fecha de aceptación no puede estar vencida.")
        finding.risk_acceptance_until = payload.risk_acceptance_until
        changes["risk_acceptance_until"] = payload.risk_acceptance_until.isoformat()

    if payload.status is not None and payload.status.value != old_status:
        target = payload.status.value
        if target not in ALLOWED_TRANSITIONS.get(old_status, set()):
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "invalid_transition",
                    "message": f"Transición no permitida: {old_status} -> {target}.",
                },
            )
        if target == FindingStatus.RESOLVED.value:
            check = _latest_check(db, finding)
            passing = check is not None and check.status == CheckStatus.PASSED
            if not passing:
                is_admin = "admin" in user.role_codes
                note = payload.resolution_note or ""
                if not is_admin or len(note.strip()) < 20:
                    raise HTTPException(
                        status_code=409,
                        detail={
                            "code": "resolution_requires_evidence",
                            "message": (
                                "El cierre requiere una comprobación satisfactoria. Solo un "
                                "administrador puede cerrarlo con una justificación documentada."
                            ),
                        },
                    )
            finding.resolved_at = now
            finding.resolved_by_run_id = finding.last_seen_run_id if passing else None
            finding.resolution_note = payload.resolution_note or finding.resolution_note
        elif old_status == FindingStatus.RESOLVED.value:
            finding.resolved_at = None
            finding.resolved_by_run_id = None
            finding.resolution_note = None
        if target == FindingStatus.FALSE_POSITIVE.value:
            finding.resolution_note = payload.resolution_note or payload.comment
            finding.resolved_at = now
        if target == FindingStatus.RISK_ACCEPTED.value:
            if not payload.risk_acceptance_until:
                raise HTTPException(
                    status_code=422, detail="Debe indicar la fecha límite de aceptación."
                )
            finding.risk_acceptance_until = payload.risk_acceptance_until
        finding.status = payload.status
        changes["status"] = {"from": old_status, "to": target}
        db.add(
            FindingEvent(
                finding_id=finding.id,
                actor_id=user.id,
                event_type="status_changed",
                from_status=old_status,
                to_status=target,
                comment=payload.comment or payload.resolution_note,
                event_metadata={},
            )
        )

    record_audit(
        db,
        action="findings.update",
        module="findings",
        organization_id=user.organization_id,
        user=user,
        resource_type="finding",
        resource_id=str(finding.id),
        request=request,
        changes={**changes, "comment": payload.comment},
    )
    db.commit()
    return get_finding(finding.id, user, db, user)


def _recommendation_out(db: Session, item: RemediationRecommendation) -> RecommendationOut:
    finding = db.get(Finding, item.finding_id)
    server = db.get(Server, finding.server_id) if finding else None
    control = db.get(CisControl, finding.control_id) if finding else None
    return RecommendationOut(
        **{
            column.name: getattr(item, column.name)
            for column in RemediationRecommendation.__table__.columns
        },
        created_by_name=_user_name(db, item.created_by_id),
        reviewed_by_name=_user_name(db, item.reviewed_by_id),
        finding_title=finding.title if finding else None,
        server_name=server.name if server else None,
        control_code=control.code if control else None,
    )


def _recommendation_detail(db: Session, item: RemediationRecommendation) -> RecommendationDetail:
    reviews = db.scalars(
        select(RemediationReview)
        .where(RemediationReview.recommendation_id == item.id)
        .order_by(RemediationReview.created_at.asc())
    ).all()
    return RecommendationDetail(
        **_recommendation_out(db, item).model_dump(),
        reviews=[
            RecommendationReviewOut(
                id=review.id,
                recommendation_id=review.recommendation_id,
                reviewer_id=review.reviewer_id,
                decision=review.decision,
                comments=review.comments,
                created_at=review.created_at,
                reviewer_name=_user_name(db, review.reviewer_id),
            )
            for review in reviews
        ],
    )


@router.post(
    "/findings/{finding_id}/recommendations",
    response_model=GenerateRecommendationResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_recommendation(
    finding_id: UUID,
    request: Request,
    user: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("recommendations:generate")),
) -> GenerateRecommendationResponse:
    finding = _get_finding(db, finding_id, user.organization_id)
    if finding.status in (FindingStatus.RESOLVED, FindingStatus.FALSE_POSITIVE):
        raise HTTPException(status_code=409, detail="No se generan recomendaciones para un hallazgo cerrado.")
    check = _latest_check(db, finding)
    context = AIContext(
        finding=finding,
        control=finding.control,
        server=finding.server,
        check=check,
    )
    try:
        result = build_recommendation(context)
    except AIUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "ai_unavailable", "message": str(exc)},
        ) from exc
    except AIInvalidResponseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "ai_invalid_response", "message": str(exc)},
        ) from exc

    db.execute(
        update(RemediationRecommendation)
        .where(
            RemediationRecommendation.finding_id == finding.id,
            RemediationRecommendation.status == RecommendationStatus.PENDING_REVIEW,
        )
        .values(status=RecommendationStatus.SUPERSEDED, updated_at=datetime.now(timezone.utc))
    )
    recommendation = RemediationRecommendation(
        organization_id=user.organization_id,
        finding_id=finding.id,
        check_id=check.id if check else None,
        source=RecommendationSource.AI,
        provider=result["provider"],
        model=result["model"],
        status=RecommendationStatus.PENDING_REVIEW,
        payload=result["payload"],
        confidence=Decimal(str(result["confidence"])),
        validation_status=result["validation_status"],
        validation_warnings=result["warnings"],
        flagged_commands=result["flags"],
        created_by_id=user.id,
    )
    db.add(recommendation)
    db.flush()
    record_audit(
        db,
        action="recommendations.generate",
        module="recommendations",
        organization_id=user.organization_id,
        user=user,
        resource_type="remediation_recommendation",
        resource_id=str(recommendation.id),
        request=request,
        changes={
            "finding_id": str(finding.id),
            "validation_status": recommendation.validation_status,
            "flagged_commands": len(result["flags"]),
        },
    )
    db.commit()
    return GenerateRecommendationResponse(
        recommendation=_recommendation_out(db, recommendation),
        ai_available=True,
        message=(
            "Propuesta generada. No se ejecutará ningún comando: requiere revisión humana."
        ),
    )


@router.get("/recommendations", response_model=Page[RecommendationOut])
def list_recommendations(
    user: CurrentUser,
    db: DbSession,
    page_params: Pagination,
    _: User = Depends(require_permission("recommendations:read")),
    recommendation_status: str | None = Query(default=None, alias="status", max_length=30),
    finding_id: UUID | None = None,
    server_id: UUID | None = None,
) -> Page[RecommendationOut]:
    page, page_size = page_params
    conditions = [RemediationRecommendation.organization_id == user.organization_id]
    if recommendation_status:
        conditions.append(RemediationRecommendation.status == recommendation_status)
    if finding_id:
        conditions.append(RemediationRecommendation.finding_id == finding_id)
    query = select(RemediationRecommendation).where(*conditions)
    if server_id:
        query = query.join(Finding, Finding.id == RemediationRecommendation.finding_id).where(
            Finding.server_id == server_id
        )
    total = int(
        db.scalar(
            select(func.count()).select_from(query.order_by(None).subquery())
        )
        or 0
    )
    items = db.scalars(
        query.order_by(RemediationRecommendation.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return Page(
        items=[_recommendation_out(db, item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/recommendations/{recommendation_id}", response_model=RecommendationDetail)
def get_recommendation(
    recommendation_id: UUID,
    user: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("recommendations:read")),
) -> RecommendationDetail:
    item = db.scalar(
        select(RemediationRecommendation).where(
            RemediationRecommendation.id == recommendation_id,
            RemediationRecommendation.organization_id == user.organization_id,
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Recomendación no encontrada.")
    return _recommendation_detail(db, item)


@router.post(
    "/recommendations/{recommendation_id}/review",
    response_model=RecommendationDetail,
)
def review_recommendation(
    recommendation_id: UUID,
    payload: RecommendationReviewIn,
    request: Request,
    user: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("recommendations:review")),
) -> RecommendationDetail:
    item = db.scalar(
        select(RemediationRecommendation).where(
            RemediationRecommendation.id == recommendation_id,
            RemediationRecommendation.organization_id == user.organization_id,
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Recomendación no encontrada.")
    if item.status != RecommendationStatus.PENDING_REVIEW:
        raise HTTPException(status_code=409, detail="La recomendación ya fue revisada.")
    if payload.decision == "approved" and item.validation_status == "dangerous":
        raise HTTPException(
            status_code=422,
            detail={
                "code": "dangerous_commands",
                "message": (
                    "No se puede aprobar una propuesta con comandos destructivos. "
                    "Rechácela y solicite una nueva propuesta."
                ),
            },
        )
    now = datetime.now(timezone.utc)
    item.status = (
        RecommendationStatus.APPROVED if payload.decision == "approved" else RecommendationStatus.REJECTED
    )
    item.reviewed_by_id = user.id
    item.reviewed_at = now
    item.review_note = payload.comments
    db.add(
        RemediationReview(
            recommendation_id=item.id,
            reviewer_id=user.id,
            decision=payload.decision,
            comments=payload.comments,
        )
    )
    record_audit(
        db,
        action=f"recommendations.{payload.decision}",
        module="recommendations",
        organization_id=user.organization_id,
        user=user,
        resource_type="remediation_recommendation",
        resource_id=str(item.id),
        request=request,
        changes={"decision": payload.decision, "comments": payload.comments},
    )
    db.commit()
    return _recommendation_detail(db, item)
