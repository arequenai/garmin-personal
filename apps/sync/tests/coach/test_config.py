from __future__ import annotations

import httpx
import pytest

from app.coach import config as coach_config

CSV_OK = (
    "key,value,unit,notes\n"
    "base_kcal,2500,kcal,\n"
    "body_weight_kg,72,kg,\n"
    "target_sleep_hours,8.0,h,\n"
    "protein_g_per_kg,2.0,g/kg,\n"
    "sleep_latency_min,15,min,\n"
    "dinner_carb_cap_g,90,g,\n"
    "dinner_protein_cap_g,55,g,\n"
)


def _mock_transport(text: str, status: int = 200):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, text=text)

    return httpx.MockTransport(handler)


def test_csv_well_formed_parses(monkeypatch):
    def fake_get(url, timeout, follow_redirects=True):
        return httpx.Response(200, text=CSV_OK)

    monkeypatch.setattr(coach_config.httpx, "get", fake_get)

    cfg, flags = coach_config.load(url="http://example/csv")
    assert flags == []
    assert cfg["base_kcal"] == 2500
    assert cfg["body_weight_kg"] == 72
    assert cfg["target_sleep_hours"] == pytest.approx(8.0)
    assert cfg["protein_g_per_kg"] == pytest.approx(2.0)


def test_missing_keys_use_defaults(monkeypatch):
    csv = "key,value,unit,notes\nbase_kcal,2500,,\n"
    monkeypatch.setattr(coach_config.httpx, "get", lambda *a, **k: httpx.Response(200, text=csv))

    cfg, flags = coach_config.load(url="http://example/csv")
    assert flags == []
    assert cfg["base_kcal"] == 2500
    assert cfg["body_weight_kg"] == coach_config.DEFAULTS["body_weight_kg"]
    assert cfg["protein_g_per_kg"] == coach_config.DEFAULTS["protein_g_per_kg"]


def test_404_returns_defaults_with_flag(monkeypatch):
    monkeypatch.setattr(coach_config.httpx, "get", lambda *a, **k: httpx.Response(404, text=""))
    cfg, flags = coach_config.load(url="http://example/csv")
    assert flags == ["config_fetch_failed"]
    assert cfg == coach_config.DEFAULTS


def test_timeout_returns_defaults_with_flag(monkeypatch):
    def boom(*a, **k):
        raise httpx.ConnectTimeout("boom")

    monkeypatch.setattr(coach_config.httpx, "get", boom)
    cfg, flags = coach_config.load(url="http://example/csv")
    assert flags == ["config_fetch_failed"]
    assert cfg == coach_config.DEFAULTS


def test_no_url_returns_defaults_with_flag(monkeypatch):
    monkeypatch.delenv("COACH_CONFIG_SHEET_CSV_URL", raising=False)
    cfg, flags = coach_config.load(url="")
    assert flags == ["config_fetch_failed"]
    assert cfg == coach_config.DEFAULTS


def test_cache_within_ttl_skips_http(monkeypatch):
    calls = {"n": 0}

    def fake_get(*a, **k):
        calls["n"] += 1
        return httpx.Response(200, text=CSV_OK)

    monkeypatch.setattr(coach_config.httpx, "get", fake_get)

    coach_config.load(url="http://example/csv", now=1000.0)
    coach_config.load(url="http://example/csv", now=1000.0 + coach_config.TTL_SECONDS - 1)
    assert calls["n"] == 1


def test_cache_invalidates_on_url_change(monkeypatch):
    calls = {"n": 0}

    def fake_get(*a, **k):
        calls["n"] += 1
        return httpx.Response(200, text=CSV_OK)

    monkeypatch.setattr(coach_config.httpx, "get", fake_get)

    coach_config.load(url="http://example/csv1", now=1000.0)
    coach_config.load(url="http://example/csv2", now=1000.0)
    assert calls["n"] == 2


def test_bad_value_falls_back_to_default_for_that_key(monkeypatch):
    csv = "key,value,unit,notes\nbase_kcal,not-a-number,,\nbody_weight_kg,80,,\n"
    monkeypatch.setattr(coach_config.httpx, "get", lambda *a, **k: httpx.Response(200, text=csv))

    cfg, flags = coach_config.load(url="http://example/csv")
    assert flags == []
    assert cfg["base_kcal"] == coach_config.DEFAULTS["base_kcal"]
    assert cfg["body_weight_kg"] == 80
