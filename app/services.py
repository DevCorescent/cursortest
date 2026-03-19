import json
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import AuditLog


def calculate_net_salary(basic_salary: Decimal, allowances: Decimal, deductions: Decimal) -> Decimal:
    return (basic_salary + allowances) - deductions


def write_audit_log(
    db: Session,
    *,
    actor_user_id: int | None,
    action: str,
    entity: str,
    entity_id: int | None = None,
    metadata: dict | None = None,
) -> None:
    entry = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        metadata_json=json.dumps(metadata or {}),
        created_at=datetime.now(timezone.utc),
    )
    db.add(entry)
