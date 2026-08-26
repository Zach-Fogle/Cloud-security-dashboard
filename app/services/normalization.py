from datetime import datetime
from typing import Any, Dict

from pydantic import ValidationError

from app.schemas import FindingCreate


AWS_SEVERITIES = {"CRITICAL": "critical", "HIGH": "high", "MEDIUM": "medium", "LOW": "low", "INFORMATIONAL": "informational"}
AWS_STATUSES = {"NEW": "open", "NOTIFIED": "in_progress", "RESOLVED": "resolved", "SUPPRESSED": "suppressed"}
AZURE_SEVERITIES = {"high": "high", "medium": "medium", "low": "low", "informational": "informational"}
AZURE_STATUSES = {"active": "open", "inprogress": "in_progress", "resolved": "resolved", "dismissed": "suppressed", "acceptedrisk": "accepted_risk"}


def _required(value: Any, name: str) -> Any:
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError("missing required field: %s" % name)
    return value


def normalize_aws(record: Dict[str, Any]) -> FindingCreate:
    severity = str(record.get("Severity", {}).get("Label", "")).upper()
    status = str(record.get("Workflow", {}).get("Status", "NEW")).upper()
    resources = record.get("Resources") or []
    if not resources:
        raise ValueError("missing required field: Resources[0]")
    resource = resources[0]
    product_fields = record.get("ProductFields") or {}
    return FindingCreate(
        source="aws_security_hub",
        source_finding_id=_required(record.get("Id"), "Id"),
        title=_required(record.get("Title"), "Title"),
        description=_required(record.get("Description"), "Description"),
        severity=_required(AWS_SEVERITIES.get(severity), "recognized Severity.Label"),
        status=_required(AWS_STATUSES.get(status), "recognized Workflow.Status"),
        cloud_provider="aws",
        account_id=_required(record.get("AwsAccountId"), "AwsAccountId"),
        resource_type=_required(resource.get("Type"), "Resources[0].Type"),
        resource_id=_required(resource.get("Id"), "Resources[0].Id"),
        application=_required(product_fields.get("Application"), "ProductFields.Application"),
        owner=_required(product_fields.get("Owner"), "ProductFields.Owner"),
        environment=_required(product_fields.get("Environment"), "ProductFields.Environment"),
        first_detected_at=_required(record.get("FirstObservedAt"), "FirstObservedAt"),
        due_date=product_fields.get("DueDate"),
        remediation_guidance=_required((record.get("Remediation") or {}).get("Recommendation", {}).get("Text"), "Remediation.Recommendation.Text"),
        resolution_note=product_fields.get("ResolutionNote"),
    )


def normalize_azure(record: Dict[str, Any]) -> FindingCreate:
    props = record.get("properties") or {}
    resource = props.get("resourceDetails") or {}
    metadata = props.get("metadata") or {}
    severity = str(props.get("severity", "")).lower()
    status = str(props.get("status", "active")).replace("_", "").replace(" ", "").lower()
    return FindingCreate(
        source="microsoft_defender_cloud",
        source_finding_id=_required(record.get("id"), "id"),
        title=_required(props.get("displayName"), "properties.displayName"),
        description=_required(props.get("description"), "properties.description"),
        severity=_required(AZURE_SEVERITIES.get(severity), "recognized properties.severity"),
        status=_required(AZURE_STATUSES.get(status), "recognized properties.status"),
        cloud_provider="azure",
        account_id=_required(resource.get("subscriptionId"), "properties.resourceDetails.subscriptionId"),
        resource_type=_required(resource.get("resourceType"), "properties.resourceDetails.resourceType"),
        resource_id=_required(resource.get("resourceId"), "properties.resourceDetails.resourceId"),
        application=_required(metadata.get("application"), "properties.metadata.application"),
        owner=_required(metadata.get("owner"), "properties.metadata.owner"),
        environment=_required(metadata.get("environment"), "properties.metadata.environment"),
        first_detected_at=_required(props.get("timeGenerated"), "properties.timeGenerated"),
        due_date=metadata.get("dueDate"),
        remediation_guidance=_required(props.get("remediationDescription"), "properties.remediationDescription"),
        resolution_note=metadata.get("resolutionNote"),
    )


def normalize_record(source: str, record: Dict[str, Any]) -> FindingCreate:
    normalizers = {"aws_security_hub": normalize_aws, "microsoft_defender_cloud": normalize_azure}
    if source not in normalizers:
        raise ValueError("unsupported source: %s" % source)
    return normalizers[source](record)
