from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models import FindingStatus, Severity


class FindingCreate(BaseModel):
    source: str = Field(min_length=1, max_length=50)
    source_finding_id: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(min_length=1)
    severity: Severity
    status: FindingStatus = FindingStatus.open
    cloud_provider: str = Field(min_length=1, max_length=30)
    account_id: str = Field(min_length=1, max_length=255)
    resource_type: str = Field(min_length=1, max_length=255)
    resource_id: str = Field(min_length=1, max_length=1000)
    application: str = Field(min_length=1, max_length=255)
    owner: str = Field(min_length=1, max_length=255)
    environment: str = Field(min_length=1, max_length=100)
    first_detected_at: datetime
    due_date: Optional[date] = None
    remediation_guidance: str = Field(min_length=1)
    resolution_note: Optional[str] = None

    @model_validator(mode="after")
    def resolved_requires_note(self):
        if self.status == FindingStatus.resolved and not (self.resolution_note or "").strip():
            raise ValueError("resolution_note is required when status is resolved")
        return self


class FindingUpdate(BaseModel):
    owner: Optional[str] = Field(default=None, min_length=1, max_length=255)
    status: Optional[FindingStatus] = None
    due_date: Optional[date] = None
    resolution_note: Optional[str] = None


class StatusAuditRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    old_status: str
    new_status: str
    changed_at: datetime


class FindingRead(FindingCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime
    updated_at: datetime
    overdue: bool = False
    audit_history: List[StatusAuditRead] = []


class ImportRequest(BaseModel):
    source: str
    records: List[Dict[str, Any]]


class ImportError(BaseModel):
    index: int
    source_finding_id: Optional[str] = None
    error: str


class ImportResult(BaseModel):
    imported: int
    duplicates: int
    errors: List[ImportError]
