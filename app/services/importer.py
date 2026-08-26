from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Finding
from app.schemas import ImportError, ImportResult
from app.services.normalization import normalize_record


def import_records(db: Session, source: str, records):
    imported = duplicates = 0
    errors = []
    for index, raw in enumerate(records):
        source_id = raw.get("Id") or raw.get("id") if isinstance(raw, dict) else None
        try:
            normalized = normalize_record(source, raw)
            exists = db.query(Finding).filter_by(source=normalized.source, source_finding_id=normalized.source_finding_id).first()
            if exists:
                duplicates += 1
                continue
            db.add(Finding(**normalized.model_dump(mode="python")))
            db.commit()
            imported += 1
        except Exception as exc:
            db.rollback()
            errors.append(ImportError(index=index, source_finding_id=source_id, error=str(exc)))
    return ImportResult(imported=imported, duplicates=duplicates, errors=errors)
