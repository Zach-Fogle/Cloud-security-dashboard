from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Finding, FindingStatus, Severity, StatusAudit
from app.schemas import FindingCreate, FindingRead, FindingUpdate, ImportRequest, ImportResult
from app.services.importer import import_records

router = APIRouter(prefix="/api", tags=["findings"])


def serialize(finding):
    data = FindingRead.model_validate(finding).model_dump()
    data["overdue"] = finding.is_overdue()
    return data


@router.post("/imports", response_model=ImportResult)
def import_findings(payload: ImportRequest, db: Session = Depends(get_db)):
    return import_records(db, payload.source, payload.records)


@router.get("/findings")
def list_findings(
    severity: Optional[Severity] = None, status_value: Optional[FindingStatus] = Query(None, alias="status"),
    owner: Optional[str] = None, application: Optional[str] = None, provider: Optional[str] = None,
    overdue: Optional[bool] = None, search: Optional[str] = None, db: Session = Depends(get_db),
):
    query = db.query(Finding)
    for column, value in [(Finding.severity, severity.value if severity else None), (Finding.status, status_value.value if status_value else None), (Finding.owner, owner), (Finding.application, application), (Finding.cloud_provider, provider)]:
        if value is not None:
            query = query.filter(column == value)
    if search:
        pattern = "%%%s%%" % search
        query = query.filter(Finding.title.ilike(pattern) | Finding.resource_id.ilike(pattern) | Finding.source_finding_id.ilike(pattern))
    findings = query.order_by(Finding.created_at.desc()).all()
    if overdue is not None:
        findings = [item for item in findings if item.is_overdue() is overdue]
    return [serialize(item) for item in findings]


@router.get("/findings/{finding_id}")
def get_finding(finding_id: str, db: Session = Depends(get_db)):
    finding = db.get(Finding, finding_id)
    if not finding:
        raise HTTPException(404, "Finding not found")
    return serialize(finding)


@router.post("/findings", status_code=status.HTTP_201_CREATED)
def create_finding(payload: FindingCreate, db: Session = Depends(get_db)):
    finding = Finding(**payload.model_dump(mode="python"))
    db.add(finding)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "A finding with this source and source_finding_id already exists")
    db.refresh(finding)
    return serialize(finding)


@router.patch("/findings/{finding_id}")
def update_finding(finding_id: str, payload: FindingUpdate, db: Session = Depends(get_db)):
    finding = db.get(Finding, finding_id)
    if not finding:
        raise HTTPException(404, "Finding not found")
    updates = payload.model_dump(exclude_unset=True, mode="python")
    next_status = updates.get("status", finding.status)
    if hasattr(next_status, "value"):
        next_status = next_status.value
        updates["status"] = next_status
    next_note = updates.get("resolution_note", finding.resolution_note)
    if next_status == FindingStatus.resolved.value and not (next_note or "").strip():
        raise HTTPException(422, "resolution_note is required when status is resolved")
    if "status" in updates and next_status != finding.status:
        db.add(StatusAudit(finding_id=finding.id, old_status=finding.status, new_status=next_status))
    for key, value in updates.items():
        setattr(finding, key, value)
    db.commit()
    db.refresh(finding)
    return serialize(finding)


@router.get("/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    findings = db.query(Finding).all()
    active = [f for f in findings if f.status not in (FindingStatus.resolved.value, FindingStatus.suppressed.value, FindingStatus.accepted_risk.value)]
    def counts(field):
        result = {}
        for finding in findings:
            key = getattr(finding, field)
            result[key] = result.get(key, 0) + 1
        return result
    return {
        "total_open": len(active),
        "critical": sum(f.severity == Severity.critical.value for f in active),
        "high": sum(f.severity == Severity.high.value for f in active),
        "overdue": sum(f.is_overdue() for f in findings),
        "by_severity": counts("severity"), "by_team": counts("owner"), "by_provider": counts("cloud_provider"),
    }
