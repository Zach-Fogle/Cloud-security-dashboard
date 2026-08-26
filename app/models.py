import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Severity(str, enum.Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    informational = "informational"


class FindingStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    suppressed = "suppressed"
    accepted_risk = "accepted_risk"


class Finding(Base):
    __tablename__ = "findings"
    __table_args__ = (UniqueConstraint("source", "source_finding_id", name="uq_source_finding"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source = Column(String(50), nullable=False)
    source_finding_id = Column(String(255), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False, index=True)
    status = Column(String(30), nullable=False, default=FindingStatus.open.value, index=True)
    cloud_provider = Column(String(30), nullable=False, index=True)
    account_id = Column(String(255), nullable=False)
    resource_type = Column(String(255), nullable=False)
    resource_id = Column(String(1000), nullable=False)
    application = Column(String(255), nullable=False, index=True)
    owner = Column(String(255), nullable=False, index=True)
    environment = Column(String(100), nullable=False)
    first_detected_at = Column(DateTime(timezone=True), nullable=False)
    due_date = Column(Date, nullable=True)
    remediation_guidance = Column(Text, nullable=False)
    resolution_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)
    audit_history = relationship("StatusAudit", back_populates="finding", cascade="all, delete-orphan")

    def is_overdue(self, today=None):
        from datetime import date
        today = today or date.today()
        return bool(self.due_date and self.due_date < today and self.status != FindingStatus.resolved.value)


class StatusAudit(Base):
    __tablename__ = "status_audits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    finding_id = Column(String(36), ForeignKey("findings.id"), nullable=False, index=True)
    old_status = Column(String(30), nullable=False)
    new_status = Column(String(30), nullable=False)
    changed_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    finding = relationship("Finding", back_populates="audit_history")
