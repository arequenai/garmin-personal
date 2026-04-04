import json
import logging
from datetime import date

import gspread
from google.oauth2.service_account import Credentials
from sqlalchemy.orm import Session

from app.models import DailySummary, NutritionDaily, PerformanceMetric, SleepSession
from app.models.body_composition import BodyComposition
from app.models.tp_fitness_data import TPFitnessData
from app.models.training_readiness import TrainingReadiness

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

HEADERS = [
    "Date",
    "Cal Total",
    "Cal Active",
    "Distance (km)",
    "Resting HR",
    "Stress Avg",
    "Body Battery High",
    "Body Battery Low",
    "Sleep Score",
    "Total Sleep (hrs)",
    "HRV",
    "Recovery Score",
    "TSS",
    "ATL",
    "CTL",
    "TSB",
    "VO2max",
    "Weight (kg)",
    "Body Fat %",
    "Training Readiness",
    "Cal (nutrition)",
    "Protein (g)",
    "Carbs (g)",
    "Fat (g)",
    "Fiber (g)",
]


def _val(value, decimals=None, as_int=False):
    """Format a value for the spreadsheet. Returns '' for None."""
    if value is None:
        return ""
    if as_int:
        return int(round(value))
    if decimals is not None:
        return round(value, decimals)
    return value


class GoogleSheetsExporter:
    def __init__(self, db: Session, spreadsheet_id: str, credentials_json: str):
        self.db = db
        self.spreadsheet_id = spreadsheet_id
        self.credentials_json = credentials_json

    def _open_spreadsheet(self):
        creds_dict = json.loads(self.credentials_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        client = gspread.authorize(creds)
        return client.open_by_key(self.spreadsheet_id)

    def _build_row(self, target_date: date) -> list:
        daily = self.db.query(DailySummary).filter_by(date=target_date).first()
        sleep = self.db.query(SleepSession).filter_by(date=target_date).first()
        tp = self.db.query(TPFitnessData).filter_by(date=target_date).first()
        perf = self.db.query(PerformanceMetric).filter_by(date=target_date).first()
        body = self.db.query(BodyComposition).filter_by(date=target_date).first()
        tr = self.db.query(TrainingReadiness).filter_by(date=target_date).first()
        nutr = self.db.query(NutritionDaily).filter_by(date=target_date).first()

        distance_km = round(daily.distance_m / 1000, 1) if daily and daily.distance_m else ""
        sleep_hrs = round(sleep.total_sleep_min / 60, 1) if sleep and sleep.total_sleep_min else ""

        return [
            target_date.isoformat(),
            _val(daily.calories_total if daily else None),
            _val(daily.calories_active if daily else None),
            distance_km,
            _val(daily.resting_hr if daily else None),
            _val(daily.stress_avg if daily else None),
            _val(daily.body_battery_high if daily else None),
            _val(daily.body_battery_low if daily else None),
            _val(sleep.sleep_score if sleep else None),
            sleep_hrs,
            _val(sleep.avg_hrv if sleep else None, decimals=1),
            _val(perf.recovery_score if perf else None, decimals=1),
            _val(tp.tss_day if tp else None, decimals=1),
            _val(tp.atl if tp else None, decimals=1),
            _val(tp.ctl if tp else None, decimals=1),
            _val(tp.tsb if tp else None, decimals=1),
            _val(perf.vo2max if perf else None, decimals=1),
            _val(body.weight_kg if body else None, decimals=1),
            _val(body.body_fat_pct if body else None, decimals=1),
            _val(tr.score if tr else None),
            _val(nutr.calories if nutr else None),
            _val(nutr.protein_g if nutr else None, decimals=1),
            _val(nutr.carbs_g if nutr else None, decimals=1),
            _val(nutr.fat_g if nutr else None, decimals=1),
            _val(nutr.fiber_g if nutr else None, decimals=1),
        ]

    def export(self, target_date: date) -> None:
        spreadsheet = self._open_spreadsheet()
        ws = spreadsheet.sheet1
        row = self._build_row(target_date)
        date_str = target_date.isoformat()

        existing_dates = ws.col_values(1)

        if not existing_dates:
            ws.append_row(HEADERS)
            ws.append_row(row)
            return

        if date_str in existing_dates:
            row_idx = existing_dates.index(date_str) + 1
            last_col = chr(64 + len(HEADERS))
            ws.update(f"A{row_idx}:{last_col}{row_idx}", [row])
        else:
            ws.append_row(row)
