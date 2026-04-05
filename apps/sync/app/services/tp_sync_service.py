import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.tp_completed_workout import TPCompletedWorkout
from app.models.tp_fitness_data import TPFitnessData
from app.models.tp_planned_workout import TPPlannedWorkout
from app.services.trainingpeaks_client import TrainingPeaksClient

logger = logging.getLogger(__name__)


class TPSyncService:
    def __init__(self, db: Session, tp_client: TrainingPeaksClient):
        self.db = db
        self.tp = tp_client

    def _upsert(self, model_class, unique_field: str, unique_value, values: dict):
        """Generic upsert: find by unique field, update or create.

        Flushes but does NOT commit — callers commit after a logical batch.
        """
        record = (
            self.db.query(model_class)
            .filter(getattr(model_class, unique_field) == unique_value)
            .first()
        )
        if record:
            for key, val in values.items():
                setattr(record, key, val)
        else:
            record = model_class(**values)
            self.db.add(record)
        self.db.flush()
        return record

    def sync_fitness(self, target_date: date) -> None:
        """Sync daily PMC data from TrainingPeaks for a single day."""
        self.sync_fitness_range(target_date, target_date)

    def sync_fitness_range(self, start: date, end: date) -> None:
        """Sync daily PMC data from TrainingPeaks for a date range (single API call)."""
        data = self.tp.get_fitness(start.isoformat(), end.isoformat())
        for entry in data:
            raw = entry.get("workoutDay") or entry.get("date") or entry.get("calendarDate")
            if not raw:
                continue
            entry_date = self._parse_date(raw)
            values = {
                "date": entry_date,
                "ctl": entry.get("ctl"),
                "atl": entry.get("atl"),
                "tsb": entry.get("tsb"),
                "tss_day": entry.get("tssActual", entry.get("tpiTssActual")),
                "intensity_factor": entry.get("ifActual"),
            }
            self._upsert(TPFitnessData, "date", entry_date, values)
        self.db.commit()

    @staticmethod
    def _parse_date(raw: str) -> date:
        """Parse date from TP, handling both '2026-03-28' and '2026-03-28T00:00:00' formats."""
        return date.fromisoformat(raw[:10])

    def sync_planned_workouts(self, target_date: date) -> None:
        """Sync planned workouts for the next 30 days."""
        start = target_date
        end = target_date + timedelta(days=30)
        workouts = self.tp.get_workouts(start.isoformat(), end.isoformat())
        for w in workouts:
            workout_id = str(w.get("workoutId", ""))
            if not workout_id:
                continue
            is_completed = w.get("completed") or w.get("tssActual") or w.get("totalTime")
            values = {
                "tp_workout_id": workout_id,
                "date": self._parse_date(w["workoutDay"]),
                "title": w.get("title"),
                "workout_type": self._resolve_workout_type(w),
                "description": w.get("description"),
                "duration_sec_planned": int(w["totalTimePlanned"] * 3600) if w.get("totalTimePlanned") else None,
                "tss_planned": w.get("tssPlanned"),
                "distance_m_planned": w.get("distancePlanned"),
                "structure_json": w.get("structure"),
                "completed": bool(is_completed),
            }
            self._upsert(TPPlannedWorkout, "tp_workout_id", workout_id, values)
        self.db.commit()

    def sync_completed_workouts(self, target_date: date) -> None:
        """Sync completed workouts for the last 7 days with zone data."""
        self.sync_completed_workouts_range(target_date - timedelta(days=7), target_date)

    def sync_completed_workouts_range(self, start: date, end: date) -> None:
        """Sync completed workouts for an arbitrary date range with zone data."""
        workouts = self.tp.get_workouts(start.isoformat(), end.isoformat())
        for w in workouts:
            # v6 API doesn't set completed=True; detect via actual data
            if not (w.get("completed") or w.get("tssActual") or w.get("totalTime")):
                continue
            workout_id = str(w.get("workoutId", ""))
            if not workout_id:
                continue

            values = {
                "tp_workout_id": workout_id,
                "date": self._parse_date(w["workoutDay"]),
                "title": w.get("title"),
                "workout_type": self._resolve_workout_type(w),
                "description": w.get("description"),
                "duration_sec": int(w["totalTime"] * 3600) if w.get("totalTime") else None,
                "distance_m": w.get("distance"),
                "tss": w.get("tpiTssActual") or w.get("tssActual"),
                "intensity_factor": w.get("if") or w.get("ifActual"),
                "avg_hr": w.get("heartRateAverage"),
                "max_hr": w.get("heartRateMaximum"),
                "avg_power": w.get("powerAverage"),
                "max_power": w.get("powerMaximum"),
                "normalized_power": w.get("normalizedPowerActual") or w.get("normalizedPower"),
                "calories": w.get("calories") or w.get("caloriesUsed"),
            }

            details = self.tp.get_workout_details(workout_id)
            if details:
                values.update(self._extract_zones(details))

            self._upsert(TPCompletedWorkout, "tp_workout_id", workout_id, values)
        self.db.commit()

    def sync_all(self, target_date: date) -> None:
        """Run all TP sync steps. Each step is isolated so one failure doesn't block others."""
        self.sync_fitness(target_date)
        try:
            self.sync_planned_workouts(target_date)
        except Exception:
            logger.warning("TP planned workouts sync failed for %s", target_date, exc_info=True)
        try:
            self.sync_completed_workouts(target_date)
        except Exception:
            logger.warning("TP completed workouts sync failed for %s", target_date, exc_info=True)

    # TP v6 workoutTypeValueId mapping
    _TYPE_MAP: dict[int, str] = {
        1: "Swim",
        2: "Bike",
        3: "Run",
        4: "Brick",
        5: "Cross-Training",
        6: "Race",
        7: "Day Off",
        8: "Note",
        9: "Strength",
        10: "Walk",
        11: "Hike",
        100: "Other",
    }

    @classmethod
    def _resolve_workout_type(cls, workout: dict) -> str | None:
        """Extract workout type string from TP workout data."""
        # v6 API: numeric workoutTypeValueId
        type_id = workout.get("workoutTypeValueId")
        if isinstance(type_id, int):
            return cls._TYPE_MAP.get(type_id, f"Type-{type_id}")
        # v1 fallback: nested dict or string
        wt = workout.get("workoutType")
        if isinstance(wt, dict):
            return wt.get("description") or wt.get("name")
        if isinstance(wt, str):
            return wt
        return None

    @staticmethod
    def _extract_zones(details: dict) -> dict:
        """Extract HR and power zone seconds from workout details (v6 format)."""
        result = {}
        hr_data = details.get("timeInHeartRateZones") or {}
        hr_zones = hr_data.get("timeInZones") or []
        for i, zone in enumerate(hr_zones[:5], 1):
            result[f"hr_zone{i}_sec"] = int(zone.get("seconds", 0))

        power_data = details.get("timeInPowerZones") or {}
        power_zones = power_data.get("timeInZones") or []
        for i, zone in enumerate(power_zones[:7], 1):
            result[f"power_zone{i}_sec"] = int(zone.get("seconds", 0))

        return result
