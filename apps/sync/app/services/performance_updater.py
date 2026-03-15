"""PerformanceUpdater: aggregates daily TSS, calculates ATL/CTL/TSB/recovery, syncs fitness metrics,
and computes category scores."""

import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.constants import RUNNING_TYPES, STRENGTH_TYPE
from app.models import Activity, DailySummary, PerformanceMetric, SleepSession
from app.models.body_composition import BodyComposition
from app.models.training_readiness import TrainingReadiness
from app.services.calculations import (
    calculate_ewma,
    calculate_recovery_score,
    calculate_tsb,
)
from app.services.recovery_model import predict_recovery

logger = logging.getLogger(__name__)

# ── Scoring targets (used to normalize 0-100 scores) ──
CTL_TARGET = 60  # Chronic training load considered "fit"
WEEKLY_KM_TARGET = 50  # Weekly running volume target (km)
WEEKLY_RUNS_TARGET = 4  # Running sessions per week
WEEKLY_STRENGTH_SESSIONS_TARGET = 4  # Strength sessions per week
WEEKLY_STRENGTH_MINUTES_TARGET = 240  # Total strength training minutes per week
TSB_OFFSET = 20  # Shift TSB range so -20..+20 maps to 0..100
TSB_RANGE = 40  # Width of the TSB scoring range
BODY_FAT_BEST = 10  # Body fat % scored as 100
BODY_FAT_WORST = 30  # Body fat % scored as 0
BMI_IDEAL = 22  # BMI ideal target
BMI_PENALTY_SCALE = 10  # Points lost per BMI unit away from ideal


class PerformanceUpdater:
    def __init__(self, db: Session, garmin=None):
        self.db = db
        self.garmin = garmin

    def update(self, target_date: date) -> None:
        # Fetch only date + TSS (not full ORM objects) for efficiency
        rows = (
            self.db.query(Activity.date, Activity.tss)
            .filter(Activity.date <= target_date)
            .order_by(Activity.date)
            .all()
        )

        # Aggregate TSS per day
        tss_by_date: dict[date, float] = {}
        for act_date, tss in rows:
            tss_by_date[act_date] = tss_by_date.get(act_date, 0) + (tss or 0)

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

        # Recovery score — prefer ML model, fall back to formula
        sleep = self.db.query(SleepSession).filter_by(date=target_date).first()
        sleep_score = sleep.sleep_score if sleep else None
        hrv = sleep.avg_hrv if sleep else None

        daily = self.db.query(DailySummary).filter_by(date=target_date).first()
        resting_hr = daily.resting_hr if daily else None
        stress_avg = daily.stress_avg if daily else None
        bb_high = daily.body_battery_high if daily else None

        recovery = predict_recovery(resting_hr, sleep_score, stress_avg, bb_high)
        if recovery is None:
            # Fallback to old formula
            recovery = calculate_recovery_score(tsb, sleep_score, hrv)

        daily_tss = tss_by_date.get(target_date, 0.0)

        values: dict = {
            "date": target_date,
            "tss": daily_tss,
            "atl": atl,
            "ctl": ctl,
            "tsb": tsb,
            "training_load_7d": round(sum(last_7), 1),
            "training_load_28d": round(sum(last_28), 1),
            "recovery_score": recovery,
        }

        # Sync fitness metrics from Garmin if client available
        if self.garmin:
            fitness = self._fetch_fitness_metrics(target_date)
            values.update(fitness)

        # Compute category scores
        category_scores = self._compute_category_scores(target_date, ctl, tsb, recovery, sleep)
        values["category_scores"] = category_scores

        # Upsert
        record = self.db.query(PerformanceMetric).filter_by(date=target_date).first()
        if record:
            for key, val in values.items():
                setattr(record, key, val)
        else:
            record = PerformanceMetric(**values)
            self.db.add(record)
        self.db.commit()

    def _fetch_fitness_metrics(self, target_date: date) -> dict:
        """Fetch VO2max, endurance score, hill score, fitness age from Garmin."""
        result = {}
        date_str = target_date.isoformat()

        try:
            max_metrics = self.garmin.get_max_metrics(date_str)
            if max_metrics:
                # max_metrics can be a list or dict
                entry = max_metrics[0] if isinstance(max_metrics, list) else max_metrics
                generic = entry.get("generic", {})
                result["vo2max"] = generic.get("vo2MaxPreciseValue") or generic.get("vo2MaxValue")
        except Exception:
            logger.debug("Failed to fetch VO2max", exc_info=True)

        try:
            endurance = self.garmin.get_endurance_score(date_str)
            if endurance:
                result["endurance_score"] = endurance.get("overallScore")
        except Exception:
            logger.debug("Failed to fetch endurance score", exc_info=True)

        try:
            hill = self.garmin.get_hill_score(date_str)
            if hill:
                result["hill_score"] = hill.get("overallScore")
        except Exception:
            logger.debug("Failed to fetch hill score", exc_info=True)

        try:
            fitness_age = self.garmin.get_fitness_age(date_str)
            if fitness_age:
                result["fitness_age"] = fitness_age.get("fitnessAge")
        except Exception:
            logger.debug("Failed to fetch fitness age", exc_info=True)

        return result

    def _compute_category_scores(
        self,
        target_date: date,
        ctl: float,
        tsb: float,
        recovery: float | None,
        sleep: SleepSession | None,
    ) -> dict[str, int]:
        """Compute 0-100 composite scores per category."""
        scores = {}

        # Running: weighted combo of VO2max trend, CTL, training consistency
        scores["running"] = self._score_running(target_date, ctl)

        # Strength: based on training frequency and volume
        scores["strength"] = self._score_strength(target_date)

        # Recovery: training readiness + TSB + sleep score
        scores["recovery"] = self._score_recovery(target_date, tsb, recovery, sleep)

        # Sleep: sleep score directly
        scores["sleep"] = self._score_sleep(sleep)

        # Body: body composition metrics
        scores["body"] = self._score_body(target_date)

        return scores

    def _score_running(self, target_date: date, ctl: float) -> int:
        start = target_date - timedelta(days=6)
        runs = (
            self.db.query(Activity)
            .filter(
                Activity.date >= start,
                Activity.date <= target_date,
                Activity.type.in_(RUNNING_TYPES),
            )
            .all()
        )
        weekly_km = sum((a.distance_m or 0) / 1000 for a in runs)

        # Score components: CTL fitness (40%), weekly volume (30%), consistency (30%)
        ctl_score = min(100, (ctl / CTL_TARGET) * 100) if ctl else 0
        vol_score = min(100, (weekly_km / WEEKLY_KM_TARGET) * 100)
        consistency = min(100, (len(runs) / WEEKLY_RUNS_TARGET) * 100)

        return int(round(ctl_score * 0.4 + vol_score * 0.3 + consistency * 0.3))

    def _score_strength(self, target_date: date) -> int:
        start = target_date - timedelta(days=6)
        sessions = (
            self.db.query(Activity)
            .filter(
                Activity.date >= start,
                Activity.date <= target_date,
                Activity.type == STRENGTH_TYPE,
            )
            .all()
        )
        count = len(sessions)
        total_min = sum((a.duration_sec or 0) / 60 for a in sessions)

        # Score: frequency (50%), volume (50%)
        freq_score = min(100, (count / WEEKLY_STRENGTH_SESSIONS_TARGET) * 100)
        vol_score = min(100, (total_min / WEEKLY_STRENGTH_MINUTES_TARGET) * 100)

        return int(round(freq_score * 0.5 + vol_score * 0.5))

    def _score_recovery(
        self, target_date: date, tsb: float, recovery: float | None, sleep: SleepSession | None
    ) -> int:
        tr = self.db.query(TrainingReadiness).filter_by(date=target_date).first()
        tr_score = min(100, tr.score) if tr and tr.score else 50

        tsb_score = min(100, max(0, (tsb + TSB_OFFSET) / TSB_RANGE * 100)) if tsb else 50
        sleep_component = min(100, sleep.sleep_score) if sleep and sleep.sleep_score else 50

        return int(round(tr_score * 0.4 + tsb_score * 0.3 + sleep_component * 0.3))

    def _score_sleep(self, sleep: SleepSession | None) -> int:
        if not sleep or not sleep.sleep_score:
            return 0
        return min(100, sleep.sleep_score)

    def _score_body(self, target_date: date) -> int:
        bc = self.db.query(BodyComposition).filter_by(date=target_date).first()
        if not bc:
            return 0

        components = []
        if bc.body_fat_pct is not None:
            # Lower body fat is better; score 100 at BODY_FAT_BEST%, 0 at BODY_FAT_WORST%
            bf_range = BODY_FAT_WORST - BODY_FAT_BEST
            bf_score = max(0, min(100, (BODY_FAT_WORST - bc.body_fat_pct) / bf_range * 100))
            components.append(bf_score)
        if bc.bmi is not None:
            # BMI_IDEAL is ideal; score decreases as you move away
            bmi_score = max(0, min(100, 100 - abs(bc.bmi - BMI_IDEAL) * BMI_PENALTY_SCALE))
            components.append(bmi_score)

        return int(round(sum(components) / max(len(components), 1)))
