from datetime import date, timedelta

from app.models import Finding, FindingStatus


def build(status="open", due_date=None):
    return Finding(status=status,due_date=due_date)


def test_overdue_is_dynamic():
    today=date.today()
    assert build(due_date=today-timedelta(days=1)).is_overdue(today)
    assert not build(due_date=today).is_overdue(today)
    assert not build(due_date=today+timedelta(days=1)).is_overdue(today)
    assert not build(status=FindingStatus.resolved.value,due_date=today-timedelta(days=1)).is_overdue(today)
