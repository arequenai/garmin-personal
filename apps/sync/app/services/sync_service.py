from datetime import date, datetime

from sqlalchemy.orm import Session

from app.models import Activity, DailySummary, NutritionDaily, SleepSession
from app.services.garmin_client import GarminClient


class SyncService:
    def __init__(self, db: Session, garmin: GarminClient, mfp=None):
        self.db = db
        self.garmin = garmin
        self.mfp = mfp

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

    def sync_daily_summary(self, target_date: date) -> DailySummary:
        date_str = target_date.isoformat()
        stats = self.garmin.get_daily_summary(date_str)
        hr = self.garmin.get_heart_rates(date_str)
        stress = self.garmin.get_stress_data(date_str)
        bb = self.garmin.get_body_battery(date_str, date_str)
        spo2 = self.garmin.get_spo2_data(date_str)
        resp = self.garmin.get_respiration_data(date_str)
        hydration = self.garmin.get_hydration_data(date_str)

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
            "stress_avg": stress.get("overallStressLevel"),
            "stress_max": stress.get("maxStressLevel"),
            "body_battery_high": max(bb_highs) if bb_highs else None,
            "body_battery_low": min(bb_lows) if bb_lows else None,
            "spo2_avg": spo2.get("averageSpo2"),
            "respiration_avg": resp.get("avgWakingRespirationValue"),
            "hydration_ml": hydration.get("valueInML"),
        }

        return self._upsert(DailySummary, "date", target_date, values)

    def sync_sleep(self, target_date: date) -> SleepSession | None:
        date_str = target_date.isoformat()
        sleep = self.garmin.get_sleep_data(date_str)
        if not sleep or not sleep.get("dailySleepDTO"):
            return None

        dto = sleep["dailySleepDTO"]
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
            "avg_hrv": None,
            "avg_spo2_sleep": dto.get("averageSpO2Value"),
            "sleep_score": dto.get("sleepScores", {}).get("overall"),
        }

        return self._upsert(SleepSession, "date", target_date, values)

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

            record = self._upsert(Activity, "garmin_id", garmin_id, values)
            synced.append(record)

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
        }
        return self._upsert(NutritionDaily, "date", target_date, values)

    def sync_all(self, target_date: date):
        self.sync_daily_summary(target_date)
        self.sync_sleep(target_date)
        self.sync_activities(target_date)
        self.sync_nutrition(target_date)
