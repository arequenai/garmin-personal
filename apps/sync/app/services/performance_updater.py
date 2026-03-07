"""PerformanceUpdater: aggregates daily TSS and calculates ATL/CTL/TSB/recovery."""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models import Activity, PerformanceMetric, SleepSession
from app.services.calculations import (
    calculate_ewma,
    calculate_recovery_score,
    calculate_tsb,
)


class PerformanceUpdater:
    def __init__(self, db: Session):
        self.db = db

    def update(self, target_date: date) -> None:
        # Get all activities up to target_date
        activities = (
            self.db.query(Activity)
            .filter(Activity.date <= target_date)
            .order_by(Activity.date)
            .all()
        )

        # Aggregate TSS per day
        tss_by_date: dict[date, float] = {}
        for act in activities:
            tss_by_date[act.date] = tss_by_date.get(act.date, 0) + (act.tss or 0)

        # Build daily TSS series (fill missing days with 0)
        if tss_by_date:
            first_date = min(tss_by_date.keys())
        else:
            first_date = target_date

        all_tss: list[float] = []
        current = first_date
        while current <= target_date:
            all_tss.append(tss_by_date.get(current, 0.0))
            current += timedelta(days=1)

        ctl = calculate_ewma(all_tss, days=42)
        atl = calculate_ewma(all_tss, days=7)
        tsb = calculate_tsb(ctl, atl)

        # Training loads (simple sums)
        last_7 = all_tss[-7:] if len(all_tss) >= 7 else all_tss
        last_28 = all_tss[-28:] if len(all_tss) >= 28 else all_tss

        # Recovery score
        sleep = self.db.query(SleepSession).filter_by(date=target_date).first()
        sleep_score = sleep.sleep_score if sleep else None
        hrv = sleep.avg_hrv if sleep else None
        recovery = calculate_recovery_score(tsb, sleep_score, hrv)

        daily_tss = tss_by_date.get(target_date, 0.0)

        values = {
            "date": target_date,
            "tss": daily_tss,
            "atl": atl,
            "ctl": ctl,
            "tsb": tsb,
            "training_load_7d": round(sum(last_7), 1),
            "training_load_28d": round(sum(last_28), 1),
            "recovery_score": recovery,
        }

        # Upsert
        record = self.db.query(PerformanceMetric).filter_by(date=target_date).first()
        if record:
            for key, val in values.items():
                setattr(record, key, val)
        else:
            record = PerformanceMetric(**values)
            self.db.add(record)
        self.db.commit()
