from datetime import date, timedelta


def test_crud_filters_summary_and_audit(client, finding_payload):
    created=client.post("/api/findings",json=finding_payload)
    assert created.status_code == 201
    item=created.json(); finding_id=item["id"]
    assert item["overdue"] is True
    assert len(client.get("/api/findings?severity=critical&provider=aws&owner=Platform&application=Billing&overdue=true").json()) == 1
    assert client.get("/api/findings?status=resolved").json() == []
    summary=client.get("/api/dashboard/summary").json()
    assert summary["total_open"] == 1 and summary["critical"] == 1 and summary["overdue"] == 1
    missing_note=client.patch("/api/findings/"+finding_id,json={"status":"resolved"})
    assert missing_note.status_code == 422
    updated=client.patch("/api/findings/"+finding_id,json={"status":"resolved","resolution_note":"Public access removed","owner":"SRE"})
    assert updated.status_code == 200
    body=updated.json()
    assert body["overdue"] is False and body["owner"] == "SRE" and len(body["audit_history"]) == 1
    assert client.get("/api/dashboard/summary").json()["total_open"] == 0


def test_duplicate_manual_finding_returns_conflict(client, finding_payload):
    assert client.post("/api/findings",json=finding_payload).status_code == 201
    assert client.post("/api/findings",json=finding_payload).status_code == 409


def test_validation_and_not_found(client, finding_payload):
    finding_payload["severity"]="urgent"
    assert client.post("/api/findings",json=finding_payload).status_code == 422
    assert client.get("/api/findings/nope").status_code == 404
    assert client.patch("/api/findings/nope",json={"owner":"x"}).status_code == 404


def test_import_endpoint_reports_partial_errors(client):
    payload={"source":"aws_security_hub","records":[{}]}
    result=client.post("/api/imports",json=payload)
    assert result.status_code == 200 and len(result.json()["errors"]) == 1


def test_search_filter(client, finding_payload):
    client.post("/api/findings",json=finding_payload)
    assert len(client.get("/api/findings?search=database").json()) == 1
    assert client.get("/api/findings?search=nomatch").json() == []


def test_web_pages_and_health(client, finding_payload):
    item=client.post("/api/findings",json=finding_payload).json()
    assert "Cloud Security Findings" in client.get("/").text
    assert "Public database" in client.get("/findings/"+item["id"]).text
    assert client.get("/health").json() == {"status":"ok"}
