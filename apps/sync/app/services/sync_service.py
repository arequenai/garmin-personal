import logging
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.models import (
    Activity,
    BodyComposition,
    DailySummary,
    ExerciseSet,
    NutritionDaily,
    RacePrediction,
    SleepSession,
    TrainingReadiness,
)
from app.models.glucose_daily import GlucoseDaily
from app.models.stress_reading import StressReading
from app.services.calculations import (
    calculate_tss_hr,
    calculate_tss_strength,
    process_stress_data,
)
from app.services.garmin_client import GarminClient

logger = logging.getLogger(__name__)


class SyncService:
    def __init__(
        self, db: Session, garmin: GarminClient, mfp=None, nightscout=None,
        hr_threshold: int = 165,
    ):
        self.db = db
        self.garmin = garmin
        self.mfp = mfp
        self.nightscout = nightscout
        self.hr_threshold = hr_threshold

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

    def sync_daily_summary(
        self, target_date: date, stress_data: dict | None = None
    ) -> DailySummary:
        date_str = target_date.isoformat()
        stats = self.garmin.get_daily_summary(date_str)
        hr = self.garmin.get_heart_rates(date_str)
        bb = self.garmin.get_body_battery(date_str, date_str)
        spo2 = self.garmin.get_spo2_data(date_str)
        resp = self.garmin.get_respiration_data(date_str)
        hydration = self.garmin.get_hydration_data(date_str)

        try:
            intensity = self.garmin.get_intensity_minutes(date_str)
            intensity_mod = intensity.get("moderateIntensityMinutes")
            intensity_vig = intensity.get("vigorousIntensityMinutes")
        except Exception:
            logger.debug("Failed to fetch intensity minutes", exc_info=True)
            intensity_mod = None
            intensity_vig = None

        # Reuse pre-fetched stress data when available to avoid duplicate API call
        stress = stress_data if stress_data is not None else self.garmin.get_stress_data(date_str)
        stress_detail = stress.get("stressValuesArray", [])
        if stress_detail:
            stress_result = process_stress_data(stress_detail)
            stress_avg = stress_result["stress_avg"]
            stress_max = stress_result["stress_max"]
        else:
            stress_avg = stress.get("overallStressLevel")
            stress_max = stress.get("maxStressLevel")

        bb_highs = [b.get("charged", 0) for b in bb] if bb else []
        bb_lows = [b.get("drained", 100) for b in bb] if bb else []

        values = {
            "date": target_date,
            "steps": stats.get("totalSteps"),
            "calories_total": stats.get("totalKilocalories"),
            "calories_active": stats.get("activeKilocalories"),
            "distance_m": stats.get("totalDistanceMeters"),
            "floors": stats.get("floorsAscended"),
            "avg_hr": hr.get("restingHeartRate"),
            "resting_hr": hr.get("restingHeartRate"),
            "max_hr": hr.get("maxHeartRate"),
            "min_hr": hr.get("minHeartRate"),
            "stress_avg": stress_avg,
            "stress_max": stress_max,
            "body_battery_high": max(bb_highs) if bb_highs else None,
            "body_battery_low": min(bb_lows) if bb_lows else None,
            "spo2_avg": spo2.get("averageSpo2"),
            "respiration_avg": resp.get("avgWakingRespirationValue"),
            "hydration_ml": hydration.get("valueInML"),
            "intensity_minutes_moderate": intensity_mod,
            "intensity_minutes_vigorous": intensity_vig,
        }

        return self._upsert(DailySummary, "date", target_date, values)

    def sync_sleep(self, target_date: date) -> SleepSession | None:
        date_str = target_date.isoformat()
        sleep = self.garmin.get_sleep_data(date_str)
        if not sleep or not sleep.get("dailySleepDTO"):
            return None

        dto = sleep["dailySleepDTO"]

        # Get HRV data to populate avg_hrv
        hrv_value = None
        try:
            hrv_data = self.garmin.get_hrv_data(date_str)
            if hrv_data:
                hrv_summary = hrv_data.get("hrvSummary", {})
                hrv_value = hrv_summary.get("lastNightAvg") or hrv_summary.get("weeklyAvg")
        except Exception:
            logger.debug("Failed to fetch HRV data", exc_info=True)

        values = {
            "date": target_date,
            "sleep_start": (
                datetime.fromtimestamp(dto["sleepStartTimestampLocal"] / 1000)
                if dto.get("sleepStartTimestampLocal")
                else None
            ),
            "sleep_end": (
                datetime.fromtimestamp(dto["sleepEndTimestampLocal"] / 1000)
                if dto.get("sleepEndTimestampLocal")
                else None
            ),
            "total_sleep_min": (
                dto["sleepTimeSeconds"] // 60 if dto.get("sleepTimeSeconds") else None
            ),
            "deep_min": dto["deepSleepSeconds"] // 60 if dto.get("deepSleepSeconds") else None,
            "light_min": dto["lightSleepSeconds"] // 60 if dto.get("lightSleepSeconds") else None,
            "rem_min": dto["remSleepSeconds"] // 60 if dto.get("remSleepSeconds") else None,
            "awake_min": dto["awakeSleepSeconds"] // 60 if dto.get("awakeSleepSeconds") else None,
            "avg_hr_sleep": dto.get("averageHeartRate"),
            "avg_hrv": hrv_value,
            "avg_spo2_sleep": dto.get("averageSpO2Value"),
            "sleep_score": self._extract_sleep_score(dto),
        }

        return self._upsert(SleepSession, "date", target_date, values)

    @staticmethod
    def _extract_sleep_score(dto: dict) -> int | None:
        score = dto.get("sleepScores", {}).get("overall")
        if isinstance(score, dict):
            return score.get("value")
        return score

    def sync_activities(self, target_date: date) -> list[Activity]:
        activities_raw = self.garmin.get_activities(0, 100)
        synced = []
        for act in activities_raw:
            act_date_str = act.get("startTimeLocal", "")
            try:
                act_date = datetime.strptime(act_date_str, "%Y-%m-%d %H:%M:%S").date()
            except (ValueError, TypeError):
                continue
            if act_date != target_date:
                continue

            garmin_id = str(act["activityId"])
            values = {
                "garmin_id": garmin_id,
                "date": act_date,
                "type": act.get("activityType", {}).get("typeKey"),
                "name": act.get("activityName"),
                "duration_sec": int(act.get("duration", 0)),
                "distance_m": act.get("distance"),
                "calories": act.get("calories"),
                "avg_hr": act.get("averageHR"),
                "max_hr": act.get("maxHR"),
                "avg_power": act.get("avgPower"),
                "max_power": act.get("maxPower"),
                "training_effect_aerobic": act.get("aerobicTrainingEffect"),
                "training_effect_anaerobic": act.get("anaerobicTrainingEffect"),
                "vo2max_estimate": act.get("vO2MaxValue"),
                "elevation_gain": act.get("elevationGain"),
            }

            # Calculate TSS
            act_type = values.get("type", "")
            if act_type == "strength_training":
                values["tss"] = calculate_tss_strength(
                    values.get("duration_sec", 0),
                    values.get("training_effect_aerobic"),
                )
            else:
                values["tss"] = calculate_tss_hr(
                    values.get("duration_sec", 0),
                    values.get("avg_hr"),
                    self.hr_threshold,
                )

            record = self._upsert(Activity, "garmin_id", garmin_id, values)
            synced.append(record)

            # Sync exercise sets for strength activities
            if act_type == "strength_training":
                self.sync_exercise_sets(record)

        return synced

    def sync_nutrition(self, target_date: date) -> NutritionDaily | None:
        if not self.mfp:
            return None
        data = self.mfp.get_day(target_date)
        if not data:
            return None
        values = {
            "date": target_date,
            "calories": data.get("calories"),
            "protein_g": data.get("protein_g"),
            "carbs_g": data.get("carbs_g"),
            "fat_g": data.get("fat_g"),
            "fiber_g": data.get("fiber_g"),
            "sodium_mg": data.get("sodium_mg"),
            "calories_goal": data.get("calories_goal"),
            "protein_goal_g": data.get("protein_goal_g"),
        }
        return self._upsert(NutritionDaily, "date", target_date, values)

    def sync_body_composition(self, target_date: date) -> BodyComposition | None:
        date_str = target_date.isoformat()
        try:
            data = self.garmin.get_body_composition(date_str)
        except Exception:
            logger.debug("Failed to fetch body composition", exc_info=True)
            return None
        if not data:
            return None

        # get_body_composition returns dict with 'dateWeightList' or 'totalAverage'
        weight_list = data.get("dateWeightList", [])
        entry = None
        for w in weight_list:
            w_date = w.get("calendarDate")
            if w_date == date_str:
                entry = w
                break
        if not entry:
            # Try totalAverage as fallback
            entry = data.get("totalAverage", {})
            if not entry:
                return None

        values = {
            "date": target_date,
            "weight_kg": entry.get("weight", entry.get("bodyWeight")),
            "body_fat_pct": entry.get("bodyFat"),
            "muscle_mass_kg": entry.get("muscleMass"),
            "bone_mass_kg": entry.get("boneMass"),
            "body_water_pct": entry.get("bodyWater"),
            "bmi": entry.get("bmi"),
            "visceral_fat": entry.get("visceralFat"),
        }

        # Convert weight from grams to kg if needed (Garmin sometimes returns grams)
        if values["weight_kg"] and values["weight_kg"] > 500:
            values["weight_kg"] = values["weight_kg"] / 1000

        # Fall back to MFP weight if Garmin has no weight
        if not values["weight_kg"] and self.mfp:
            mfp_weight = self.mfp.get_weight()
            if mfp_weight:
                values["weight_kg"] = mfp_weight

        return self._upsert(BodyComposition, "date", target_date, values)

    def sync_race_predictions(self, target_date: date) -> RacePrediction | None:
        date_str = target_date.isoformat()
        try:
            data = self.garmin.get_race_predictions(date_str)
        except Exception:
            logger.debug("Failed to fetch race predictions", exc_info=True)
            return None
        if not data:
            return None

        # data is a list of daily predictions
        entry = None
        if isinstance(data, list):
            for p in data:
                if p.get("calendarDate") == date_str:
                    entry = p
                    break
            if not entry and data:
                entry = data[0]  # fallback to first entry
        elif isinstance(data, dict):
            entry = data

        if not entry:
            return None

        values = {
            "date": target_date,
            "predicted_5k_sec": (
                entry.get("racePredictions", {}).get("5K", {}).get("predictedTime")
            ),
            "predicted_10k_sec": (
                entry.get("racePredictions", {}).get("10K", {}).get("predictedTime")
            ),
            "predicted_half_sec": (
                entry.get("racePredictions", {}).get("halfMarathon", {}).get("predictedTime")
            ),
            "predicted_marathon_sec": (
                entry.get("racePredictions", {}).get("marathon", {}).get("predictedTime")
            ),
        }

        return self._upsert(RacePrediction, "date", target_date, values)

    def sync_training_readiness(self, target_date: date) -> TrainingReadiness | None:
        date_str = target_date.isoformat()
        try:
            data = self.garmin.get_training_readiness(date_str)
        except Exception:
            logger.debug("Failed to fetch training readiness", exc_info=True)
            return None
        if not data:
            return None

        # API may return a list; extract first element
        if isinstance(data, list):
            data = data[0] if data else {}
        if not isinstance(data, dict):
            return None

        values = {
            "date": target_date,
            "score": data.get("score"),
            "level": data.get("level"),
            "hrv_status": data.get("hrvStatus"),
            "sleep_status": data.get("sleepStatus"),
            "recovery_status": data.get("recoveryStatus"),
        }

        return self._upsert(TrainingReadiness, "date", target_date, values)

    def sync_exercise_sets(self, activity: Activity) -> list[ExerciseSet]:
        """Sync per-set exercise data for a strength activity."""
        synced = []
        try:
            data = self.garmin.get_exercise_sets(str(activity.garmin_id))
        except Exception:
            logger.debug("Failed to fetch exercise sets for %s", activity.garmin_id, exc_info=True)
            return synced
        if not data:
            return synced

        exercises = data.get("exerciseSets", [])
        for exercise in exercises:
            exercise_name = exercise.get("exerciseName", "Unknown")
            sets = exercise.get("sets", [])
            # Garmin API doesn't provide a stable set ID; positional index is the
            # only available key. Sets are ordered by execution time, so re-syncs
            # produce the same ordering for a given activity.
            for i, s in enumerate(sets, 1):
                set_type = s.get("setType")
                reps = s.get("repetitionCount")
                weight = s.get("weight")
                duration = s.get("duration")

                # Convert weight from grams to kg
                if weight and weight > 0:
                    weight = weight / 1000

                values = {
                    "activity_id": activity.id,
                    "exercise_name": exercise_name,
                    "set_number": i,
                    "reps": reps,
                    "weight_kg": weight,
                    "duration_sec": int(duration) if duration else None,
                    "set_type": set_type,
                }

                # Use composite key for upsert
                existing = (
                    self.db.query(ExerciseSet)
                    .filter_by(
                        activity_id=activity.id,
                        exercise_name=exercise_name,
                        set_number=i,
                    )
                    .first()
                )
                if existing:
                    for key, val in values.items():
                        setattr(existing, key, val)
                    record = existing
                else:
                    record = ExerciseSet(**values)
                    self.db.add(record)
                synced.append(record)

        self.db.commit()
        return synced

    def sync_glucose(self, target_date: date) -> GlucoseDaily | None:
        """Sync glucose data from Nightscout for a target date."""
        if not self.nightscout:
            return None
        data = self.nightscout.get_daily_summary(target_date)
        if not data:
            return None
        values = {
            "date": target_date,
            "readings_count": data.get("readings_count"),
            "mean_glucose": data.get("mean_glucose"),
            "min_glucose": data.get("min_glucose"),
            "max_glucose": data.get("max_glucose"),
            "latest_glucose": data.get("latest_glucose"),
            "fasting_glucose": data.get("fasting_glucose"),
        }
        return self._upsert(GlucoseDaily, "date", target_date, values)

    def sync_stress_readings(self, target_date: date, stress_data: dict | None = None) -> int:
        """Sync raw stress data points into stress_readings table.

        Returns number of readings stored.
        """
        date_str = target_date.isoformat()
        stress = stress_data if stress_data is not None else self.garmin.get_stress_data(date_str)
        values_array = stress.get("stressValuesArray", [])
        if not values_array:
            return 0

        # Delete existing readings for this date (idempotent re-sync)
        self.db.query(StressReading).filter(StressReading.date == target_date).delete()

        count = 0
        for ts_ms, value in values_array:
            reading = StressReading(
                date=target_date,
                timestamp=datetime.fromtimestamp(ts_ms / 1000),
                value=value,
            )
            self.db.add(reading)
            count += 1

        self.db.commit()
        return count

    def sync_all(self, target_date: date):
        # Fetch stress data once and share across methods that need it
        stress_data = self.garmin.get_stress_data(target_date.isoformat())

        self.sync_daily_summary(target_date, stress_data=stress_data)
        self.sync_sleep(target_date)
        self.sync_activities(target_date)
        self.sync_nutrition(target_date)
        self.sync_body_composition(target_date)
        self.sync_race_predictions(target_date)
        self.sync_training_readiness(target_date)
        self.sync_glucose(target_date)
        self.sync_stress_readings(target_date, stress_data=stress_data)
