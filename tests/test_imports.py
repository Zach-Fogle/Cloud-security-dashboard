from app.models import Finding
from app.services.importer import import_records


def raw(identifier="a"):
    return {"Id":identifier,"AwsAccountId":"1","Title":"T","Description":"D","Severity":{"Label":"HIGH"},"Workflow":{"Status":"NEW"},"Resources":[{"Type":"Bucket","Id":"b"}],"FirstObservedAt":"2026-01-01T00:00:00Z","ProductFields":{"Application":"App","Owner":"Team","Environment":"prod"},"Remediation":{"Recommendation":{"Text":"Fix"}}}


def test_import_and_duplicate(db):
    first=import_records(db,"aws_security_hub",[raw()])
    second=import_records(db,"aws_security_hub",[raw()])
    assert (first.imported, second.duplicates, db.query(Finding).count()) == (1,1,1)


def test_individual_errors_do_not_block_valid_records(db):
    result=import_records(db,"aws_security_hub",[{},raw("good")])
    assert result.imported == 1 and len(result.errors) == 1 and result.errors[0].index == 0
