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
        """Generic upsert: find by unique field, update or create."""
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
        self.db.commit()
        self.db.refresh(record)
        return record

    def sync_fitness(self, target_date: date) -> None:
        """Sync daily PMC data from TrainingPeaks."""
        date_str = target_date.isoformat()
        data = self.tp.get_fitness(date_str, date_str)
        for entry in data:
            entry_date_str = entry.get("date") or entry.get("calendarDate")
            if not entry_date_str:
                continue
            entry_date = date.fromisoformat(entry_date_str)
            values = {
                "date": entry_date,
                "ctl": entry.get("ctl"),
                "atl": entry.get("atl"),
                "tsb": entry.get("tsb"),
                "tss_day": entry.get("tpiTssActual") or entry.get("tssActual"),
                "training_load_7d": entry.get("trainingLoad7d"),
                "training_load_28d": entry.get("trainingLoad28d"),
                "intensity_factor": entry.get("ifActual"),
                "ramp_rate": entry.get("rampRate"),
            }
            self._upsert(TPFitnessData, "date", entry_date, values)

    def sync_planned_workouts(self, target_date: date) -> None:
        """Sync planned workouts for the next 30 days."""
        start = target_date
        end = target_date + timedelta(days=30)
        workouts = self.tp.get_workouts(start.isoformat(), end.isoformat())
        for w in workouts:
            workout_id = str(w.get("workoutId", ""))
            if not workout_id:
                continue
            values = {
                "tp_workout_id": workout_id,
                "date": date.fromisoformat(w["workoutDay"]),
                "title": w.get("title"),
                "workout_type": self._resolve_workout_type(w),
                "description": w.get("description"),
                "duration_sec_planned": w.get("totalTimePlanned"),
                "tss_planned": w.get("tssPlanned"),
                "distance_m_planned": w.get("distancePlanned"),
                "structure_json": w.get("structure"),
                "completed": w.get("completed", False),
            }
            self._upsert(TPPlannedWorkout, "tp_workout_id", workout_id, values)

    def sync_completed_workouts(self, target_date: date) -> None:
        """Sync completed workouts for the last 7 days with zone data."""
        start = target_date - timedelta(days=7)
        end = target_date
        workouts = self.tp.get_workouts(start.isoformat(), end.isoformat())
        for w in workouts:
            if not w.get("completed"):
                continue
            workout_id = str(w.get("workoutId", ""))
            if not workout_id:
                continue

            values = {
                "tp_workout_id": workout_id,
                "date": date.fromisoformat(w["workoutDay"]),
                "title": w.get("title"),
                "workout_type": self._resolve_workout_type(w),
                "duration_sec": w.get("totalTime"),
                "distance_m": w.get("distance"),
                "tss": w.get("tpiTssActual") or w.get("tssActual"),
                "intensity_factor": w.get("ifActual"),
                "avg_hr": w.get("heartRateAverage"),
                "max_hr": w.get("heartRateMaximum"),
                "avg_power": w.get("powerAverage"),
                "max_power": w.get("powerMaximum"),
                "normalized_power": w.get("normalizedPower"),
                "calories": w.get("caloriesUsed"),
            }

            analysis = self.tp.get_workout_analysis(workout_id)
            if analysis:
                values.update(self._extract_zones(analysis))
                values["laps_json"] = analysis.get("laps")

            self._upsert(TPCompletedWorkout, "tp_workout_id", workout_id, values)

    def sync_all(self, target_date: date) -> None:
        """Run all TP sync steps."""
        self.sync_fitness(target_date)
        self.sync_planned_workouts(target_date)
        self.sync_completed_workouts(target_date)

    @staticmethod
    def _resolve_workout_type(workout: dict) -> str | None:
        """Extract workout type string from TP workout data."""
        wt = workout.get("workoutType")
        if isinstance(wt, dict):
            return wt.get("description") or wt.get("name")
        if isinstance(wt, str):
            return wt
        return None

    @staticmethod
    def _extract_zones(analysis: dict) -> dict:
        """Extract HR and power zone seconds from workout analysis."""
        result = {}
        hr_zones = analysis.get("heartRateZones", [])
        for i, zone in enumerate(hr_zones[:5], 1):
            result[f"hr_zone{i}_sec"] = zone.get("timeInZone")

        power_zones = analysis.get("powerZones", [])
        for i, zone in enumerate(power_zones[:7], 1):
            result[f"power_zone{i}_sec"] = zone.get("timeInZone")

        return result
