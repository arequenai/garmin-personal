from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import DailySummary, NutritionDaily, PerformanceMetric, SleepSession
from app.models.body_composition import BodyComposition
from app.models.training_readiness import TrainingReadiness
from app.services.sheets_exporter import HEADERS, GoogleSheetsExporter
from app.services.sync_orchestrator import run_sync_for_date


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


@pytest.fixture
def target_date():
    return date(2026, 4, 4)


def _seed_full_data(db, target_date):
    """Insert one row into each table for target_date."""
    db.add(
        DailySummary(
            date=target_date,
            calories_total=2500,
            calories_active=800,
            distance_m=8500.0,
            resting_hr=52,
            stress_avg=30,
            body_battery_high=80,
            body_battery_low=25,
        )
    )
    db.add(
        SleepSession(
            date=target_date,
            sleep_score=82,
            total_sleep_min=450,
            avg_hrv=45.0,
        )
    )
    db.add(
        PerformanceMetric(
            date=target_date,
            recovery_score=72.3,
            tss=85.6,
            atl=65.2,
            ctl=55.8,
            tsb=-9.4,
            vo2max=48.3,
        )
    )
    db.add(
        BodyComposition(
            date=target_date,
            weight_kg=75.4,
            body_fat_pct=15.2,
        )
    )
    db.add(
        TrainingReadiness(
            date=target_date,
            score=68,
        )
    )
    db.add(
        NutritionDaily(
            date=target_date,
            calories=2200,
            protein_g=150.0,
            carbs_g=250.0,
            fat_g=80.0,
            fiber_g=30.0,
        )
    )
    db.commit()


def _make_mock_worksheet(existing_dates=None):
    """Create a mock gspread worksheet.

    Args:
        existing_dates: list of date strings already in col A (excluding header).
            None means the sheet is completely empty (no header, no data).
    """
    mock_ws = MagicMock()
    if existing_dates is None:
        mock_ws.col_values.return_value = []
    else:
        mock_ws.col_values.return_value = ["Date"] + existing_dates
    return mock_ws


def _make_exporter(db, mock_ws):
    """Create exporter with a patched gspread client."""
    exporter = GoogleSheetsExporter(
        db=db,
        spreadsheet_id="fake-id",
        credentials_json='{"type": "service_account"}',
    )
    mock_spreadsheet = MagicMock()
    mock_spreadsheet.sheet1 = mock_ws
    exporter._open_spreadsheet = MagicMock(return_value=mock_spreadsheet)
    return exporter


def test_export_writes_headers_on_empty_sheet(db_session, target_date):
    _seed_full_data(db_session, target_date)
    mock_ws = _make_mock_worksheet(existing_dates=None)
    exporter = _make_exporter(db_session, mock_ws)

    exporter.export(target_date)

    mock_ws.append_row.assert_any_call(HEADERS)
    assert mock_ws.append_row.call_count == 2
    data_row = mock_ws.append_row.call_args_list[1][0][0]
    assert data_row[0] == "2026-04-04"


def test_export_appends_new_date(db_session, target_date):
    _seed_full_data(db_session, target_date)
    mock_ws = _make_mock_worksheet(existing_dates=["2026-04-03"])
    exporter = _make_exporter(db_session, mock_ws)

    exporter.export(target_date)

    mock_ws.append_row.assert_called_once()
    data_row = mock_ws.append_row.call_args[0][0]
    assert data_row[0] == "2026-04-04"


def test_export_updates_existing_date(db_session, target_date):
    _seed_full_data(db_session, target_date)
    mock_ws = _make_mock_worksheet(existing_dates=["2026-04-04"])
    exporter = _make_exporter(db_session, mock_ws)

    exporter.export(target_date)

    mock_ws.update.assert_called_once()
    call_args = mock_ws.update.call_args
    assert call_args[0][0] == f"A2:{chr(64 + len(HEADERS))}2"
    updated_row = call_args[0][1][0]
    assert updated_row[0] == "2026-04-04"
    mock_ws.append_row.assert_not_called()


def test_export_with_missing_db_records(db_session, target_date):
    db_session.add(
        DailySummary(
            date=target_date,
            calories_total=2500,
            resting_hr=52,
        )
    )
    db_session.commit()

    mock_ws = _make_mock_worksheet(existing_dates=[])
    exporter = _make_exporter(db_session, mock_ws)

    exporter.export(target_date)

    data_row = mock_ws.append_row.call_args[0][0]
    assert data_row[0] == "2026-04-04"
    assert data_row[1] == 2500
    assert data_row[8] == ""
    assert data_row[11] == ""
    assert data_row[20] == ""


def test_export_converts_units(db_session, target_date):
    _seed_full_data(db_session, target_date)
    mock_ws = _make_mock_worksheet(existing_dates=[])
    exporter = _make_exporter(db_session, mock_ws)

    exporter.export(target_date)

    data_row = mock_ws.append_row.call_args[0][0]
    assert data_row[3] == 8.5
    assert data_row[9] == 7.5
    assert data_row[11] == 72
    assert data_row[12] == 85.6


@patch("app.services.sync_orchestrator.settings")
@patch("app.services.sync_orchestrator.SessionLocal")
@patch("app.services.sync_orchestrator.GarminClient")
@patch("app.services.sync_orchestrator.PerformanceUpdater")
@patch("app.services.sync_orchestrator.SyncService")
@patch("app.services.sync_orchestrator.GoogleSheetsExporter")
def test_orchestrator_calls_exporter_when_configured(
    mock_exporter_cls,
    mock_sync_cls,
    mock_perf_cls,
    mock_garmin_cls,
    mock_session_cls,
    mock_settings,
):
    mock_settings.garmin_email = "test@test.com"
    mock_settings.garmin_password = "pass"
    mock_settings.mfp_cookies = ""
    mock_settings.nightscout_url = ""
    mock_settings.nightscout_token = ""
    mock_settings.google_service_account_json = '{"type": "service_account"}'
    mock_settings.google_spreadsheet_id = "sheet-id"

    mock_db = MagicMock()
    mock_session_cls.return_value = mock_db
    mock_db.query.return_value.first.return_value = None

    run_sync_for_date(date(2026, 4, 4))

    mock_exporter_cls.assert_called_once_with(
        db=mock_db,
        spreadsheet_id="sheet-id",
        credentials_json='{"type": "service_account"}',
    )
    mock_exporter_cls.return_value.export.assert_called_once_with(date(2026, 4, 4))


@patch("app.services.sync_orchestrator.settings")
@patch("app.services.sync_orchestrator.SessionLocal")
@patch("app.services.sync_orchestrator.GarminClient")
@patch("app.services.sync_orchestrator.PerformanceUpdater")
@patch("app.services.sync_orchestrator.SyncService")
@patch("app.services.sync_orchestrator.GoogleSheetsExporter")
def test_orchestrator_skips_exporter_when_not_configured(
    mock_exporter_cls,
    mock_sync_cls,
    mock_perf_cls,
    mock_garmin_cls,
    mock_session_cls,
    mock_settings,
):
    mock_settings.garmin_email = "test@test.com"
    mock_settings.garmin_password = "pass"
    mock_settings.mfp_cookies = ""
    mock_settings.nightscout_url = ""
    mock_settings.nightscout_token = ""
    mock_settings.google_service_account_json = ""
    mock_settings.google_spreadsheet_id = ""

    mock_db = MagicMock()
    mock_session_cls.return_value = mock_db
    mock_db.query.return_value.first.return_value = None

    run_sync_for_date(date(2026, 4, 4))

    mock_exporter_cls.assert_not_called()


@patch("app.services.sync_orchestrator.settings")
@patch("app.services.sync_orchestrator.SessionLocal")
@patch("app.services.sync_orchestrator._get_garmin_client")
@patch("app.services.sync_orchestrator.GoogleSheetsExporter")
def test_orchestrator_exports_sheets_even_when_garmin_login_fails(
    mock_exporter_cls,
    mock_get_garmin,
    mock_session_cls,
    mock_settings,
):
    """Sheets export must run even when Garmin login raises."""
    mock_get_garmin.side_effect = Exception("429 Too Many Requests")
    mock_settings.google_service_account_json = '{"type": "service_account"}'
    mock_settings.google_spreadsheet_id = "sheet-id"
    mock_settings.tp_enabled = False
    mock_settings.tp_auth_cookie = ""

    mock_db = MagicMock()
    mock_session_cls.return_value = mock_db

    run_sync_for_date(date(2026, 4, 4))

    mock_exporter_cls.assert_called_once()
    mock_exporter_cls.return_value.export.assert_called_once_with(date(2026, 4, 4))
