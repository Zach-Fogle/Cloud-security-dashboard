import pytest

from app.services.normalization import normalize_record


def test_aws_normalization_maps_fields():
    raw={"Id":"a","AwsAccountId":"1","Title":"T","Description":"D","Severity":{"Label":"CRITICAL"},"Workflow":{"Status":"NOTIFIED"},"Resources":[{"Type":"Bucket","Id":"b"}],"FirstObservedAt":"2026-01-01T00:00:00Z","ProductFields":{"Application":"App","Owner":"Team","Environment":"prod"},"Remediation":{"Recommendation":{"Text":"Fix"}}}
    finding=normalize_record("aws_security_hub",raw)
    assert finding.severity.value == "critical" and finding.status.value == "in_progress"
    assert finding.cloud_provider == "aws" and finding.resource_id == "b"


def test_azure_normalization_maps_accepted_risk():
    raw={"id":"a","properties":{"displayName":"T","description":"D","severity":"Medium","status":"AcceptedRisk","timeGenerated":"2026-01-01T00:00:00Z","resourceDetails":{"subscriptionId":"s","resourceType":"VM","resourceId":"v"},"metadata":{"application":"App","owner":"Team","environment":"prod"},"remediationDescription":"Fix"}}
    finding=normalize_record("microsoft_defender_cloud",raw)
    assert finding.status.value == "accepted_risk" and finding.cloud_provider == "azure"


@pytest.mark.parametrize("source", ["unknown", "AWS"])
def test_unknown_source_rejected(source):
    with pytest.raises(ValueError, match="unsupported source"):
        normalize_record(source,{})


def test_malformed_import_record_has_helpful_error():
    with pytest.raises(ValueError, match="missing required field"):
        normalize_record("aws_security_hub",{"Id":"x"})
