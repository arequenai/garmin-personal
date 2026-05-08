from datetime import date

from sqlalchemy.orm import Session

from app.models.coach_briefing import CoachBriefing


def get_briefing(db: Session, target_date: date, kind: str) -> CoachBriefing | None:
    return (
        db.query(CoachBriefing)
        .filter(CoachBriefing.date == target_date, CoachBriefing.kind == kind)
        .one_or_none()
    )


def get_last_briefing(db: Session) -> CoachBriefing | None:
    return (
        db.query(CoachBriefing)
        .order_by(CoachBriefing.sent_at.desc())
        .first()
    )


def save_briefing(
    db: Session,
    *,
    target_date: date,
    kind: str,
    inputs_json: dict,
    recommendation_json: dict,
    semaphore: str,
    llm_used: bool,
    llm_text: str | None,
    flags: list[str],
    ntfy_status_code: int | None,
) -> CoachBriefing:
    row = CoachBriefing(
        date=target_date,
        kind=kind,
        inputs_json=inputs_json,
        recommendation_json=recommendation_json,
        semaphore=semaphore,
        llm_used=llm_used,
        llm_text=llm_text,
        flags=flags,
        ntfy_status_code=ntfy_status_code,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
