# Personal Health Dashboard — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a personal health & performance dashboard that syncs data from Garmin Connect and MyFitnessPal, calculates training load metrics (TSS/ATL/CTL/TSB), and displays everything in an elegant dark-themed webapp.

**Architecture:** Monorepo with Next.js 14+ frontend (App Router + Tailwind) and Python FastAPI backend for API + Garmin/MFP sync. PostgreSQL in Docker. Single user, no auth.

**Tech Stack:** Next.js, TypeScript, Tailwind CSS, Recharts, FastAPI, SQLAlchemy, Alembic, garminconnect, APScheduler, NumPy, PostgreSQL 16, Docker.

---

## Phase 1: Infrastructure & Project Scaffolding

### Task 1: Docker + PostgreSQL

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `.gitignore`

**Step 1: Create docker-compose.yml**

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: garmin_personal
      POSTGRES_USER: garmin
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-garmin_dev}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

**Step 2: Create .env.example**

```env
POSTGRES_PASSWORD=garmin_dev
DATABASE_URL=postgresql://garmin:garmin_dev@localhost:5432/garmin_personal

GARMIN_EMAIL=your@email.com
GARMIN_PASSWORD=your_password

MFP_USERNAME=your_username
MFP_PASSWORD=your_password

HR_MAX=190
HR_REST=50
HR_THRESHOLD=165
```

**Step 3: Create .gitignore**

Standard Python + Node + env gitignore. Include:
```
.env
__pycache__/
*.pyc
node_modules/
.next/
dist/
.venv/
*.egg-info/
pgdata/
```

**Step 4: Start PostgreSQL and verify**

```bash
docker compose up -d
docker compose exec db psql -U garmin -d garmin_personal -c "SELECT 1;"
```

Expected: Connection successful, returns `1`.

**Step 5: Commit**

```bash
git add docker-compose.yml .env.example .gitignore
git commit -m "chore: add Docker PostgreSQL setup and project gitignore"
```

---

### Task 2: Python Backend Scaffolding

**Files:**
- Create: `apps/sync/pyproject.toml`
- Create: `apps/sync/app/__init__.py`
- Create: `apps/sync/app/main.py`
- Create: `apps/sync/app/config.py`
- Create: `apps/sync/app/database.py`

**Step 1: Initialize Python project with uv**

```bash
mkdir -p apps/sync
cd apps/sync
uv init --name garmin-sync
```

**Step 2: Add dependencies to pyproject.toml**

```toml
[project]
name = "garmin-sync"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "sqlalchemy>=2.0.0",
    "alembic>=1.14.0",
    "psycopg2-binary>=2.9.0",
    "garminconnect>=0.2.0",
    "apscheduler>=3.10.0",
    "numpy>=2.0.0",
    "pydantic-settings>=2.0.0",
    "httpx>=0.28.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "ruff>=0.8.0",
]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]
```

**Step 3: Install dependencies**

```bash
cd apps/sync && uv sync
```

**Step 4: Create app/config.py**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://garmin:garmin_dev@localhost:5432/garmin_personal"
    garmin_email: str = ""
    garmin_password: str = ""
    mfp_username: str = ""
    mfp_password: str = ""
    hr_max: int = 190
    hr_rest: int = 50
    hr_threshold: int = 165

    model_config = {"env_file": "../../.env"}


settings = Settings()
```

**Step 5: Create app/database.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Step 6: Create app/main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Garmin Personal Sync")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
```

**Step 7: Verify FastAPI starts**

```bash
cd apps/sync && uv run uvicorn app.main:app --reload --port 8000
# In another terminal:
curl http://localhost:8000/api/health
```

Expected: `{"status":"ok"}`

**Step 8: Commit**

```bash
git add apps/sync/
git commit -m "feat(sync): scaffold FastAPI backend with config and database setup"
```

---

### Task 3: Next.js Frontend Scaffolding

**Files:**
- Create: `apps/web/` (via create-next-app)
- Modify: `apps/web/tailwind.config.ts` (custom theme)
- Create: `apps/web/src/app/layout.tsx` (fonts + dark theme)

**Step 1: Create Next.js app**

```bash
cd apps && pnpm create next-app@latest web --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --no-turbo
```

**Step 2: Install additional dependencies**

```bash
cd apps/web && pnpm add recharts lucide-react date-fns
pnpm add -D prettier prettier-plugin-tailwindcss
```

**Step 3: Configure Tailwind with custom theme**

Update `apps/web/tailwind.config.ts`:

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: "#0a0a0f",
          card: "#12121a",
          hover: "#1a1a25",
        },
        text: {
          primary: "#e8e8ed",
          secondary: "#6b6b7b",
        },
        recovery: "#22c55e",
        strain: "#f97316",
        sleep: "#6366f1",
        alert: "#ef4444",
      },
      fontFamily: {
        heading: ["var(--font-space-grotesk)", "sans-serif"],
        body: ["var(--font-inter)", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
```

**Step 4: Setup layout with fonts and dark base**

Update `apps/web/src/app/layout.tsx`:

```tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Space_Grotesk } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space-grotesk",
});

export const metadata: Metadata = {
  title: "Garmin Personal",
  description: "Personal health & performance dashboard",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${spaceGrotesk.variable}`}>
      <body className="bg-bg-primary font-body text-text-primary antialiased">
        {children}
      </body>
    </html>
  );
}
```

**Step 5: Update globals.css**

Replace contents of `apps/web/src/app/globals.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  * {
    @apply border-bg-hover;
  }
  body {
    @apply bg-bg-primary text-text-primary;
  }
}
```

**Step 6: Create minimal page to verify**

Update `apps/web/src/app/page.tsx`:

```tsx
export default function Home() {
  return (
    <main className="flex min-h-screen items-center justify-center">
      <h1 className="font-heading text-4xl font-bold">Garmin Personal</h1>
    </main>
  );
}
```

**Step 7: Verify it runs**

```bash
cd apps/web && pnpm dev
# Open http://localhost:3000 - should show "Garmin Personal" in Space Grotesk on dark bg
```

**Step 8: Commit**

```bash
git add apps/web/
git commit -m "feat(web): scaffold Next.js app with custom dark theme and typography"
```

---

## Phase 2: Database Models & Migrations

### Task 4: SQLAlchemy Models

**Files:**
- Create: `apps/sync/app/models/__init__.py`
- Create: `apps/sync/app/models/user.py`
- Create: `apps/sync/app/models/daily_summary.py`
- Create: `apps/sync/app/models/sleep_session.py`
- Create: `apps/sync/app/models/activity.py`
- Create: `apps/sync/app/models/strength_session.py`
- Create: `apps/sync/app/models/nutrition_daily.py`
- Create: `apps/sync/app/models/performance_metric.py`
- Create: `apps/sync/tests/test_models.py`

**Step 1: Write test for models**

Create `apps/sync/tests/__init__.py` (empty) and `apps/sync/tests/test_models.py`:

```python
from app.models import (
    User,
    DailySummary,
    SleepSession,
    Activity,
    StrengthSession,
    NutritionDaily,
    PerformanceMetric,
)


def test_all_models_importable():
    assert User.__tablename__ == "users"
    assert DailySummary.__tablename__ == "daily_summaries"
    assert SleepSession.__tablename__ == "sleep_sessions"
    assert Activity.__tablename__ == "activities"
    assert StrengthSession.__tablename__ == "strength_sessions"
    assert NutritionDaily.__tablename__ == "nutrition_daily"
    assert PerformanceMetric.__tablename__ == "performance_metrics"


def test_user_has_required_columns():
    columns = {c.name for c in User.__table__.columns}
    assert "garmin_email" in columns
    assert "hr_max" in columns
    assert "hr_threshold" in columns


def test_activity_has_tss_column():
    columns = {c.name for c in Activity.__table__.columns}
    assert "tss" in columns
    assert "garmin_id" in columns


def test_strength_session_has_fk():
    columns = {c.name for c in StrengthSession.__table__.columns}
    assert "activity_id" in columns
```

**Step 2: Run test to verify it fails**

```bash
cd apps/sync && uv run pytest tests/test_models.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.models'`

**Step 3: Create model files**

`apps/sync/app/models/user.py`:
```python
from sqlalchemy import Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    garmin_email: Mapped[str] = mapped_column(String(255), default="")
    garmin_password: Mapped[str] = mapped_column(String(512), default="")
    mfp_username: Mapped[str] = mapped_column(String(255), default="")
    mfp_password: Mapped[str] = mapped_column(String(512), default="")
    hr_max: Mapped[int] = mapped_column(Integer, default=190)
    hr_rest: Mapped[int] = mapped_column(Integer, default=50)
    hr_threshold: Mapped[int] = mapped_column(Integer, default=165)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
```

`apps/sync/app/models/daily_summary.py`:
```python
from sqlalchemy import Integer, Float, Date
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DailySummary(Base):
    __tablename__ = "daily_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[Date] = mapped_column(Date, unique=True, nullable=False)
    steps: Mapped[int] = mapped_column(Integer, nullable=True)
    calories_total: Mapped[int] = mapped_column(Integer, nullable=True)
    calories_active: Mapped[int] = mapped_column(Integer, nullable=True)
    distance_m: Mapped[float] = mapped_column(Float, nullable=True)
    floors: Mapped[int] = mapped_column(Integer, nullable=True)
    avg_hr: Mapped[int] = mapped_column(Integer, nullable=True)
    resting_hr: Mapped[int] = mapped_column(Integer, nullable=True)
    max_hr: Mapped[int] = mapped_column(Integer, nullable=True)
    min_hr: Mapped[int] = mapped_column(Integer, nullable=True)
    stress_avg: Mapped[int] = mapped_column(Integer, nullable=True)
    stress_max: Mapped[int] = mapped_column(Integer, nullable=True)
    body_battery_high: Mapped[int] = mapped_column(Integer, nullable=True)
    body_battery_low: Mapped[int] = mapped_column(Integer, nullable=True)
    spo2_avg: Mapped[float] = mapped_column(Float, nullable=True)
    respiration_avg: Mapped[float] = mapped_column(Float, nullable=True)
    hydration_ml: Mapped[int] = mapped_column(Integer, nullable=True)
```

`apps/sync/app/models/sleep_session.py`:
```python
from sqlalchemy import Integer, Float, Date, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SleepSession(Base):
    __tablename__ = "sleep_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[Date] = mapped_column(Date, unique=True, nullable=False)
    sleep_start: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    sleep_end: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    total_sleep_min: Mapped[int] = mapped_column(Integer, nullable=True)
    deep_min: Mapped[int] = mapped_column(Integer, nullable=True)
    light_min: Mapped[int] = mapped_column(Integer, nullable=True)
    rem_min: Mapped[int] = mapped_column(Integer, nullable=True)
    awake_min: Mapped[int] = mapped_column(Integer, nullable=True)
    avg_hr_sleep: Mapped[int] = mapped_column(Integer, nullable=True)
    avg_hrv: Mapped[float] = mapped_column(Float, nullable=True)
    avg_spo2_sleep: Mapped[float] = mapped_column(Float, nullable=True)
    sleep_score: Mapped[int] = mapped_column(Integer, nullable=True)
```

`apps/sync/app/models/activity.py`:
```python
from sqlalchemy import Integer, Float, String, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    garmin_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    date: Mapped[Date] = mapped_column(Date, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(100), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    duration_sec: Mapped[int] = mapped_column(Integer, nullable=True)
    distance_m: Mapped[float] = mapped_column(Float, nullable=True)
    calories: Mapped[int] = mapped_column(Integer, nullable=True)
    avg_hr: Mapped[int] = mapped_column(Integer, nullable=True)
    max_hr: Mapped[int] = mapped_column(Integer, nullable=True)
    avg_power: Mapped[float] = mapped_column(Float, nullable=True)
    max_power: Mapped[float] = mapped_column(Float, nullable=True)
    training_effect_aerobic: Mapped[float] = mapped_column(Float, nullable=True)
    training_effect_anaerobic: Mapped[float] = mapped_column(Float, nullable=True)
    vo2max_estimate: Mapped[float] = mapped_column(Float, nullable=True)
    elevation_gain: Mapped[float] = mapped_column(Float, nullable=True)
    tss: Mapped[float] = mapped_column(Float, nullable=True)

    strength_sets = relationship("StrengthSession", back_populates="activity")
```

`apps/sync/app/models/strength_session.py`:
```python
from sqlalchemy import Integer, Float, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class StrengthSession(Base):
    __tablename__ = "strength_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    activity_id: Mapped[int] = mapped_column(Integer, ForeignKey("activities.id"), nullable=False)
    exercise_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sets: Mapped[int] = mapped_column(Integer, nullable=True)
    reps: Mapped[int] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=True)
    tonnage: Mapped[float] = mapped_column(Float, nullable=True)

    activity = relationship("Activity", back_populates="strength_sets")
```

`apps/sync/app/models/nutrition_daily.py`:
```python
from sqlalchemy import Integer, Float, Date
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class NutritionDaily(Base):
    __tablename__ = "nutrition_daily"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[Date] = mapped_column(Date, unique=True, nullable=False)
    calories: Mapped[int] = mapped_column(Integer, nullable=True)
    protein_g: Mapped[float] = mapped_column(Float, nullable=True)
    carbs_g: Mapped[float] = mapped_column(Float, nullable=True)
    fat_g: Mapped[float] = mapped_column(Float, nullable=True)
    fiber_g: Mapped[float] = mapped_column(Float, nullable=True)
    sodium_mg: Mapped[float] = mapped_column(Float, nullable=True)
```

`apps/sync/app/models/performance_metric.py`:
```python
from sqlalchemy import Integer, Float, Date
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[Date] = mapped_column(Date, unique=True, nullable=False)
    tss: Mapped[float] = mapped_column(Float, nullable=True)
    atl: Mapped[float] = mapped_column(Float, nullable=True)
    ctl: Mapped[float] = mapped_column(Float, nullable=True)
    tsb: Mapped[float] = mapped_column(Float, nullable=True)
    training_load_7d: Mapped[float] = mapped_column(Float, nullable=True)
    training_load_28d: Mapped[float] = mapped_column(Float, nullable=True)
    recovery_score: Mapped[float] = mapped_column(Float, nullable=True)
```

`apps/sync/app/models/__init__.py`:
```python
from app.models.user import User
from app.models.daily_summary import DailySummary
from app.models.sleep_session import SleepSession
from app.models.activity import Activity
from app.models.strength_session import StrengthSession
from app.models.nutrition_daily import NutritionDaily
from app.models.performance_metric import PerformanceMetric

__all__ = [
    "User",
    "DailySummary",
    "SleepSession",
    "Activity",
    "StrengthSession",
    "NutritionDaily",
    "PerformanceMetric",
]
```

**Step 4: Run tests**

```bash
cd apps/sync && uv run pytest tests/test_models.py -v
```

Expected: All 4 tests PASS.

**Step 5: Commit**

```bash
git add apps/sync/app/models/ apps/sync/tests/
git commit -m "feat(sync): add SQLAlchemy models for all tables"
```

---

### Task 5: Alembic Migrations

**Files:**
- Create: `apps/sync/alembic.ini`
- Create: `apps/sync/alembic/` (via alembic init)
- Modify: `apps/sync/alembic/env.py`

**Step 1: Initialize Alembic**

```bash
cd apps/sync && uv run alembic init alembic
```

**Step 2: Update alembic.ini**

Set `sqlalchemy.url` to empty (we load from env):
```ini
sqlalchemy.url =
```

**Step 3: Update alembic/env.py**

Add model imports and config loading at the top of `env.py`:

```python
from app.config import settings
from app.database import Base
from app.models import *  # noqa: F401,F403

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)
target_metadata = Base.metadata
```

**Step 4: Generate initial migration**

```bash
cd apps/sync && uv run alembic revision --autogenerate -m "create all tables"
```

**Step 5: Run migration (requires PostgreSQL running)**

```bash
cd apps/sync && uv run alembic upgrade head
```

**Step 6: Verify tables exist**

```bash
docker compose exec db psql -U garmin -d garmin_personal -c "\dt"
```

Expected: all 7 tables + alembic_version visible.

**Step 7: Commit**

```bash
git add apps/sync/alembic/ apps/sync/alembic.ini
git commit -m "feat(sync): add Alembic migrations for initial schema"
```

---

## Phase 3: Garmin Sync Service

### Task 6: Garmin Connect Client Wrapper

**Files:**
- Create: `apps/sync/app/services/__init__.py`
- Create: `apps/sync/app/services/garmin_client.py`
- Create: `apps/sync/tests/test_garmin_client.py`

**Step 1: Write test**

```python
from unittest.mock import MagicMock, patch
from app.services.garmin_client import GarminClient


def test_garmin_client_initializes():
    client = GarminClient(email="test@test.com", password="test123")
    assert client.email == "test@test.com"


@patch("app.services.garmin_client.Garmin")
def test_login_calls_garmin_connect(mock_garmin_cls):
    mock_instance = MagicMock()
    mock_garmin_cls.return_value = mock_instance
    client = GarminClient(email="test@test.com", password="test123")
    client.login()
    mock_garmin_cls.assert_called_once_with("test@test.com", "test123")
    mock_instance.login.assert_called_once()


@patch("app.services.garmin_client.Garmin")
def test_get_daily_summary(mock_garmin_cls):
    mock_instance = MagicMock()
    mock_instance.get_stats.return_value = {"totalSteps": 10000}
    mock_garmin_cls.return_value = mock_instance
    client = GarminClient(email="t@t.com", password="p")
    client.login()
    result = client.get_daily_summary("2026-03-06")
    assert result["totalSteps"] == 10000
```

**Step 2: Run test to verify it fails**

```bash
cd apps/sync && uv run pytest tests/test_garmin_client.py -v
```

**Step 3: Implement GarminClient**

```python
from garminconnect import Garmin


class GarminClient:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self._client: Garmin | None = None

    def login(self):
        self._client = Garmin(self.email, self.password)
        self._client.login()

    def get_daily_summary(self, date_str: str) -> dict:
        return self._client.get_stats(date_str)

    def get_activities(self, start: int = 0, limit: int = 20) -> list[dict]:
        return self._client.get_activities(start, limit)

    def get_activity_details(self, activity_id: str) -> dict:
        return self._client.get_activity(activity_id)

    def get_sleep_data(self, date_str: str) -> dict:
        return self._client.get_sleep_data(date_str)

    def get_heart_rates(self, date_str: str) -> dict:
        return self._client.get_heart_rates(date_str)

    def get_hrv_data(self, date_str: str) -> dict:
        return self._client.get_hrv_data(date_str)

    def get_stress_data(self, date_str: str) -> dict:
        return self._client.get_stress_data(date_str)

    def get_body_battery(self, date_str: str) -> list[dict]:
        return self._client.get_body_battery(date_str)

    def get_hydration_data(self, date_str: str) -> dict:
        return self._client.get_hydration_data(date_str)

    def get_respiration_data(self, date_str: str) -> dict:
        return self._client.get_respiration_data(date_str)

    def get_spo2_data(self, date_str: str) -> dict:
        return self._client.get_spo2_data(date_str)

    def get_steps_data(self, date_str: str) -> dict:
        return self._client.get_steps_data(date_str)
```

**Step 4: Run tests**

```bash
cd apps/sync && uv run pytest tests/test_garmin_client.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add apps/sync/app/services/ apps/sync/tests/test_garmin_client.py
git commit -m "feat(sync): add Garmin Connect client wrapper"
```

---

### Task 7: Sync Service — Daily Summary, Sleep, Activities

**Files:**
- Create: `apps/sync/app/services/sync_service.py`
- Create: `apps/sync/tests/test_sync_service.py`

**Step 1: Write tests for sync_daily_summary**

```python
from datetime import date
from unittest.mock import MagicMock

from app.services.sync_service import SyncService


def make_sync_service(db_session, garmin_data=None):
    mock_garmin = MagicMock()
    if garmin_data:
        for method, data in garmin_data.items():
            getattr(mock_garmin, method).return_value = data
    return SyncService(db=db_session, garmin=mock_garmin)
```

This test file will be expanded as we implement each sync method. Use an in-memory SQLite for tests or mock the DB session. The implementation should:

1. Call the Garmin client methods for a given date
2. Map the raw Garmin API response fields to our model columns
3. Upsert (insert or update) the record in the DB

**Step 2: Implement SyncService**

Key structure:

```python
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.models import DailySummary, SleepSession, Activity, StrengthSession
from app.services.garmin_client import GarminClient


class SyncService:
    def __init__(self, db: Session, garmin: GarminClient):
        self.db = db
        self.garmin = garmin

    def sync_daily_summary(self, target_date: date) -> DailySummary:
        date_str = target_date.isoformat()
        stats = self.garmin.get_daily_summary(date_str)
        hr = self.garmin.get_heart_rates(date_str)
        stress = self.garmin.get_stress_data(date_str)
        bb = self.garmin.get_body_battery(date_str)
        spo2 = self.garmin.get_spo2_data(date_str)
        resp = self.garmin.get_respiration_data(date_str)
        hydration = self.garmin.get_hydration_data(date_str)

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
            "body_battery_high": max((b.get("charged", 0) for b in bb), default=None) if bb else None,
            "body_battery_low": min((b.get("charged", 100) for b in bb), default=None) if bb else None,
            "spo2_avg": spo2.get("averageSpo2"),
            "respiration_avg": resp.get("avgWakingRespirationValue"),
            "hydration_ml": hydration.get("valueInML"),
        }

        stmt = insert(DailySummary).values(**values)
        stmt = stmt.on_conflict_do_update(index_elements=["date"], set_=values)
        self.db.execute(stmt)
        self.db.commit()
        return self.db.query(DailySummary).filter_by(date=target_date).first()

    def sync_sleep(self, target_date: date) -> SleepSession | None:
        date_str = target_date.isoformat()
        sleep = self.garmin.get_sleep_data(date_str)
        if not sleep or not sleep.get("dailySleepDTO"):
            return None

        dto = sleep["dailySleepDTO"]
        values = {
            "date": target_date,
            "sleep_start": datetime.fromtimestamp(dto["sleepStartTimestampLocal"] / 1000) if dto.get("sleepStartTimestampLocal") else None,
            "sleep_end": datetime.fromtimestamp(dto["sleepEndTimestampLocal"] / 1000) if dto.get("sleepEndTimestampLocal") else None,
            "total_sleep_min": dto.get("sleepTimeSeconds", 0) // 60 if dto.get("sleepTimeSeconds") else None,
            "deep_min": dto.get("deepSleepSeconds", 0) // 60 if dto.get("deepSleepSeconds") else None,
            "light_min": dto.get("lightSleepSeconds", 0) // 60 if dto.get("lightSleepSeconds") else None,
            "rem_min": dto.get("remSleepSeconds", 0) // 60 if dto.get("remSleepSeconds") else None,
            "awake_min": dto.get("awakeSleepSeconds", 0) // 60 if dto.get("awakeSleepSeconds") else None,
            "avg_hr_sleep": dto.get("averageHeartRate"),
            "avg_hrv": sleep.get("hrvData", {}).get("startTimestampLocal"),  # needs mapping from actual API
            "avg_spo2_sleep": dto.get("averageSpO2Value"),
            "sleep_score": dto.get("sleepScores", {}).get("overall"),
        }

        stmt = insert(SleepSession).values(**values)
        stmt = stmt.on_conflict_do_update(index_elements=["date"], set_=values)
        self.db.execute(stmt)
        self.db.commit()
        return self.db.query(SleepSession).filter_by(date=target_date).first()

    def sync_activities(self, target_date: date) -> list[Activity]:
        activities_raw = self.garmin.get_activities(0, 100)
        synced = []
        for act in activities_raw:
            act_date = datetime.fromisoformat(act["startTimeLocal"]).date()
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

            stmt = insert(Activity).values(**values)
            stmt = stmt.on_conflict_do_update(index_elements=["garmin_id"], set_=values)
            self.db.execute(stmt)
            self.db.commit()
            synced.append(self.db.query(Activity).filter_by(garmin_id=garmin_id).first())

        return synced

    def sync_all(self, target_date: date):
        self.sync_daily_summary(target_date)
        self.sync_sleep(target_date)
        self.sync_activities(target_date)
```

Note: The exact field mappings from Garmin's API may need adjustment when testing with real data. The `garminconnect` library documentation and actual API responses should be consulted during implementation. These mappings are best-effort based on known Garmin Connect API structure.

**Step 3: Run tests**

```bash
cd apps/sync && uv run pytest tests/ -v
```

**Step 4: Commit**

```bash
git add apps/sync/app/services/sync_service.py apps/sync/tests/
git commit -m "feat(sync): add sync service for daily summary, sleep, and activities"
```

---

## Phase 4: Performance Calculations

### Task 8: TSS Calculation

**Files:**
- Create: `apps/sync/app/services/calculations.py`
- Create: `apps/sync/tests/test_calculations.py`

**Step 1: Write tests**

```python
import pytest
from app.services.calculations import calculate_tss_hr, calculate_tss_power, calculate_tss_strength


def test_tss_hr_basic():
    # 1 hour at threshold = 100 TSS
    tss = calculate_tss_hr(duration_sec=3600, avg_hr=165, hr_threshold=165)
    assert tss == pytest.approx(100.0, rel=0.01)


def test_tss_hr_easy():
    # 1 hour at 75% of threshold
    tss = calculate_tss_hr(duration_sec=3600, avg_hr=124, hr_threshold=165)
    assert tss < 60


def test_tss_hr_hard():
    # 1 hour above threshold
    tss = calculate_tss_hr(duration_sec=3600, avg_hr=175, hr_threshold=165)
    assert tss > 100


def test_tss_hr_missing_data():
    tss = calculate_tss_hr(duration_sec=3600, avg_hr=None, hr_threshold=165)
    assert tss is None


def test_tss_power_basic():
    # 1 hour at FTP = 100 TSS
    tss = calculate_tss_power(duration_sec=3600, avg_power=250, normalized_power=250, ftp=250)
    assert tss == pytest.approx(100.0, rel=0.01)


def test_tss_strength():
    # Based on duration and training effect
    tss = calculate_tss_strength(duration_sec=3600, training_effect=3.5)
    assert tss > 0
    assert tss < 200
```

**Step 2: Run tests — expect FAIL**

```bash
cd apps/sync && uv run pytest tests/test_calculations.py -v
```

**Step 3: Implement calculations**

```python
def calculate_tss_hr(
    duration_sec: int,
    avg_hr: int | None,
    hr_threshold: int,
) -> float | None:
    if avg_hr is None or hr_threshold == 0:
        return None
    intensity_factor = avg_hr / hr_threshold
    tss = (duration_sec * intensity_factor ** 2 * 100) / 3600
    return round(tss, 1)


def calculate_tss_power(
    duration_sec: int,
    avg_power: float | None,
    normalized_power: float | None,
    ftp: float,
) -> float | None:
    if normalized_power is None or ftp == 0:
        return None
    intensity_factor = normalized_power / ftp
    tss = (duration_sec * normalized_power * intensity_factor) / (ftp * 36)
    return round(tss, 1)


def calculate_tss_strength(
    duration_sec: int,
    training_effect: float | None,
) -> float | None:
    if training_effect is None:
        return None
    # Estimate: TE 1.0 = ~20 TSS/hr, TE 5.0 = ~120 TSS/hr (linear scale)
    tss_per_hour = 20 + (training_effect - 1.0) * 25
    tss = tss_per_hour * (duration_sec / 3600)
    return round(tss, 1)
```

**Step 4: Run tests — expect PASS**

```bash
cd apps/sync && uv run pytest tests/test_calculations.py -v
```

**Step 5: Commit**

```bash
git add apps/sync/app/services/calculations.py apps/sync/tests/test_calculations.py
git commit -m "feat(sync): add TSS calculation for HR, power, and strength"
```

---

### Task 9: ATL/CTL/TSB Calculation

**Files:**
- Modify: `apps/sync/app/services/calculations.py`
- Modify: `apps/sync/tests/test_calculations.py`

**Step 1: Write tests**

```python
def test_exponential_weighted_average_empty():
    result = calculate_ewma([], days=7)
    assert result == 0.0


def test_exponential_weighted_average_single():
    result = calculate_ewma([100.0], days=7)
    assert result > 0


def test_ctl_42_day():
    # 42 days of constant 50 TSS should converge near 50
    tss_values = [50.0] * 60
    ctl = calculate_ewma(tss_values, days=42)
    assert ctl == pytest.approx(50.0, rel=0.05)


def test_atl_7_day():
    # 7 days of constant 50 TSS should converge near 50
    tss_values = [50.0] * 14
    atl = calculate_ewma(tss_values, days=7)
    assert atl == pytest.approx(50.0, rel=0.05)


def test_tsb_calculation():
    ctl = 50.0
    atl = 70.0
    tsb = calculate_tsb(ctl, atl)
    assert tsb == -20.0


def test_recovery_score():
    # Good recovery: high TSB, good sleep, high HRV
    score = calculate_recovery_score(tsb=15.0, sleep_score=85, hrv=65.0)
    assert 70 <= score <= 100

    # Bad recovery: negative TSB, bad sleep, low HRV
    score = calculate_recovery_score(tsb=-25.0, sleep_score=40, hrv=25.0)
    assert score < 50
```

**Step 2: Run tests — expect FAIL**

**Step 3: Implement**

Add to `calculations.py`:

```python
import numpy as np


def calculate_ewma(tss_values: list[float], days: int) -> float:
    if not tss_values:
        return 0.0
    decay = 2.0 / (days + 1)
    ewma = 0.0
    for tss in tss_values:
        ewma = tss * decay + ewma * (1 - decay)
    return round(ewma, 2)


def calculate_tsb(ctl: float, atl: float) -> float:
    return round(ctl - atl, 2)


def calculate_recovery_score(
    tsb: float | None,
    sleep_score: int | None,
    hrv: float | None,
) -> float:
    weights = {"tsb": 0.35, "sleep": 0.40, "hrv": 0.25}
    score = 50.0  # baseline

    if tsb is not None:
        # TSB range typically -30 to +30, normalize to 0-100
        tsb_norm = max(0, min(100, (tsb + 30) / 60 * 100))
        score += (tsb_norm - 50) * weights["tsb"]

    if sleep_score is not None:
        score += (sleep_score - 50) * weights["sleep"]

    if hrv is not None:
        # HRV range typically 20-100, normalize to 0-100
        hrv_norm = max(0, min(100, (hrv - 20) / 80 * 100))
        score += (hrv_norm - 50) * weights["hrv"]

    return round(max(0, min(100, score)), 1)
```

**Step 4: Run tests — expect PASS**

**Step 5: Commit**

```bash
git add apps/sync/app/services/calculations.py apps/sync/tests/test_calculations.py
git commit -m "feat(sync): add ATL/CTL/TSB and recovery score calculations"
```

---

### Task 10: Performance Metrics Updater

**Files:**
- Create: `apps/sync/app/services/performance_updater.py`
- Create: `apps/sync/tests/test_performance_updater.py`

This service queries all activities up to the target date, recalculates ATL/CTL/TSB, and upserts into `performance_metrics`. It also calculates 7d and 28d training loads as simple sums.

**Step 1: Write tests with mocked DB**

**Step 2: Implement PerformanceUpdater class**

```python
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.models import Activity, PerformanceMetric, SleepSession
from app.services.calculations import calculate_ewma, calculate_tsb, calculate_recovery_score


class PerformanceUpdater:
    def __init__(self, db: Session):
        self.db = db

    def update(self, target_date: date):
        # Get all TSS values ordered by date up to target_date
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
        if not tss_by_date:
            return

        first_date = min(tss_by_date.keys())
        all_tss = []
        current = first_date
        while current <= target_date:
            all_tss.append(tss_by_date.get(current, 0.0))
            current += timedelta(days=1)

        ctl = calculate_ewma(all_tss, days=42)
        atl = calculate_ewma(all_tss, days=7)
        tsb = calculate_tsb(ctl, atl)

        # 7d and 28d training loads (simple sums)
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
            "training_load_7d": sum(last_7),
            "training_load_28d": sum(last_28),
            "recovery_score": recovery,
        }

        stmt = insert(PerformanceMetric).values(**values)
        stmt = stmt.on_conflict_do_update(index_elements=["date"], set_=values)
        self.db.execute(stmt)
        self.db.commit()
```

**Step 3: Run tests — expect PASS**

**Step 4: Commit**

```bash
git add apps/sync/app/services/performance_updater.py apps/sync/tests/test_performance_updater.py
git commit -m "feat(sync): add performance metrics updater (ATL/CTL/TSB per day)"
```

---

## Phase 5: API Endpoints

### Task 11: Settings Endpoints

**Files:**
- Create: `apps/sync/app/routers/__init__.py`
- Create: `apps/sync/app/routers/settings.py`
- Create: `apps/sync/app/schemas/__init__.py`
- Create: `apps/sync/app/schemas/settings.py`
- Modify: `apps/sync/app/main.py`

**Step 1: Create Pydantic schemas**

```python
# apps/sync/app/schemas/settings.py
from pydantic import BaseModel


class SettingsResponse(BaseModel):
    hr_max: int
    hr_rest: int
    hr_threshold: int

    model_config = {"from_attributes": True}


class SettingsUpdate(BaseModel):
    hr_max: int | None = None
    hr_rest: int | None = None
    hr_threshold: int | None = None
```

**Step 2: Create router**

```python
# apps/sync/app/routers/settings.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.settings import SettingsResponse, SettingsUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])


def get_user(db: Session) -> User:
    user = db.query(User).first()
    if not user:
        user = User()
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@router.get("", response_model=SettingsResponse)
def get_settings(db: Session = Depends(get_db)):
    return get_user(db)


@router.put("", response_model=SettingsResponse)
def update_settings(data: SettingsUpdate, db: Session = Depends(get_db)):
    user = get_user(db)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user
```

**Step 3: Register router in main.py**

Add to `apps/sync/app/main.py`:
```python
from app.routers import settings
app.include_router(settings.router)
```

**Step 4: Test with curl**

```bash
curl http://localhost:8000/api/settings
curl -X PUT http://localhost:8000/api/settings -H "Content-Type: application/json" -d '{"hr_max": 185}'
```

**Step 5: Commit**

```bash
git add apps/sync/app/routers/ apps/sync/app/schemas/
git commit -m "feat(sync): add settings API endpoints"
```

---

### Task 12: Data Query Endpoints

**Files:**
- Create: `apps/sync/app/routers/dashboard.py`
- Create: `apps/sync/app/routers/activities.py`
- Create: `apps/sync/app/routers/sleep.py`
- Create: `apps/sync/app/routers/nutrition.py`
- Create: `apps/sync/app/routers/performance.py`
- Create: `apps/sync/app/routers/daily.py`
- Create: `apps/sync/app/schemas/` (response models for each)
- Modify: `apps/sync/app/main.py` (register all routers)

Each endpoint follows the same pattern:
1. Accept `from_date` and `to_date` as query params (default: last 30 days)
2. Query the relevant table
3. Return as JSON list

The dashboard/today endpoint aggregates today's data from multiple tables.

**Key endpoints to implement:**

```python
# GET /api/dashboard/today
# Returns: daily_summary + sleep + latest activity + nutrition + performance_metric for today

# GET /api/activities?from_date=2026-01-01&to_date=2026-03-06
# Returns: list of activities with all fields

# GET /api/sleep?from_date=&to_date=
# Returns: list of sleep sessions

# GET /api/nutrition?from_date=&to_date=
# Returns: list of nutrition_daily records

# GET /api/performance?from_date=&to_date=
# Returns: list of performance_metrics (ATL/CTL/TSB series)

# GET /api/daily?from_date=&to_date=
# Returns: list of daily_summaries
```

Create Pydantic response schemas for each model in `apps/sync/app/schemas/`. Use `model_config = {"from_attributes": True}` for SQLAlchemy compatibility.

**Step 1: Implement all routers and schemas (follow the settings pattern)**

**Step 2: Register in main.py**

**Step 3: Test with curl**

**Step 4: Commit**

```bash
git add apps/sync/app/routers/ apps/sync/app/schemas/
git commit -m "feat(sync): add all data query API endpoints"
```

---

### Task 13: Sync Trigger Endpoint

**Files:**
- Create: `apps/sync/app/routers/sync.py`
- Modify: `apps/sync/app/main.py`

**Step 1: Create sync router**

```python
from datetime import date, timedelta
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.services.garmin_client import GarminClient
from app.services.sync_service import SyncService
from app.services.performance_updater import PerformanceUpdater

router = APIRouter(prefix="/api/sync", tags=["sync"])


def run_sync(target_date: date, db: Session):
    garmin = GarminClient(email=settings.garmin_email, password=settings.garmin_password)
    garmin.login()
    sync = SyncService(db=db, garmin=garmin)
    sync.sync_all(target_date)
    updater = PerformanceUpdater(db=db)
    updater.update(target_date)


@router.post("/trigger")
def trigger_sync(
    background_tasks: BackgroundTasks,
    days_back: int = 1,
    db: Session = Depends(get_db),
):
    target = date.today() - timedelta(days=days_back)
    background_tasks.add_task(run_sync, target, db)
    return {"status": "sync_started", "target_date": target.isoformat()}
```

**Step 2: Register and test**

**Step 3: Commit**

```bash
git add apps/sync/app/routers/sync.py
git commit -m "feat(sync): add sync trigger endpoint with background task"
```

---

### Task 14: APScheduler Cron

**Files:**
- Create: `apps/sync/app/scheduler.py`
- Modify: `apps/sync/app/main.py`

**Step 1: Create scheduler**

```python
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import date, timedelta

from app.database import SessionLocal
from app.config import settings
from app.services.garmin_client import GarminClient
from app.services.sync_service import SyncService
from app.services.performance_updater import PerformanceUpdater


def daily_sync_job():
    db = SessionLocal()
    try:
        target = date.today() - timedelta(days=1)
        garmin = GarminClient(email=settings.garmin_email, password=settings.garmin_password)
        garmin.login()
        sync = SyncService(db=db, garmin=garmin)
        sync.sync_all(target)
        updater = PerformanceUpdater(db=db)
        updater.update(target)
    finally:
        db.close()


scheduler = BackgroundScheduler()
scheduler.add_job(daily_sync_job, "cron", hour=5, minute=0)
```

**Step 2: Wire into FastAPI lifespan**

In `main.py`, add startup/shutdown:

```python
from contextlib import asynccontextmanager
from app.scheduler import scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(title="Garmin Personal Sync", lifespan=lifespan)
```

**Step 3: Commit**

```bash
git add apps/sync/app/scheduler.py
git commit -m "feat(sync): add daily cron scheduler with APScheduler"
```

---

## Phase 6: MyFitnessPal Integration

### Task 15: MFP Sync

**Files:**
- Create: `apps/sync/app/services/mfp_client.py`
- Modify: `apps/sync/app/services/sync_service.py`

Research the current best approach for MFP data extraction (the `myfitnesspal` Python package or `httpx` scraping). Implement:

```python
class MFPClient:
    def __init__(self, username: str, password: str):
        ...

    def get_day(self, target_date: date) -> dict:
        """Returns: {calories, protein_g, carbs_g, fat_g, fiber_g, sodium_mg}"""
        ...
```

Add `sync_nutrition` method to `SyncService` that calls MFPClient and upserts into `nutrition_daily`.

Add MFP sync call to `sync_all` and to the scheduler job.

**Commit:**

```bash
git commit -m "feat(sync): add MyFitnessPal nutrition sync"
```

---

## Phase 7: Frontend — Foundation

### Task 16: Layout & Sidebar Navigation

**Files:**
- Create: `apps/web/src/components/layout/sidebar.tsx`
- Create: `apps/web/src/components/layout/app-layout.tsx`
- Modify: `apps/web/src/app/layout.tsx`
- Create: `apps/web/src/app/(dashboard)/layout.tsx`

**Step 1: Create Sidebar component**

Dark sidebar with Lucide icons. Links:
- Dashboard (Home icon) — `/`
- Performance (TrendingUp icon) — `/performance`
- Sleep (Moon icon) — `/sleep`
- Nutrition (Apple icon) — `/nutrition`
- Body (Heart icon) — `/body`

Style: narrow sidebar (64px collapsed, 200px expanded on hover or toggle), bg-bg-card, icons in text-secondary that highlight on active/hover. Logo or initials at top.

**Step 2: Create AppLayout wrapper**

```tsx
// Sidebar + main content area
export function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-8">{children}</main>
    </div>
  );
}
```

**Step 3: Create dashboard route group**

`apps/web/src/app/(dashboard)/layout.tsx`:
```tsx
import { AppLayout } from "@/components/layout/app-layout";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <AppLayout>{children}</AppLayout>;
}
```

**Step 4: Verify navigation works visually**

**Step 5: Commit**

```bash
git commit -m "feat(web): add sidebar navigation and app layout"
```

---

### Task 17: Shared UI Components

**Files:**
- Create: `apps/web/src/components/ui/metric-card.tsx`
- Create: `apps/web/src/components/ui/trend-chart.tsx`
- Create: `apps/web/src/components/ui/gauge.tsx`
- Create: `apps/web/src/components/ui/score-ring.tsx`
- Create: `apps/web/src/lib/api.ts`

**Step 1: Create API client**

```typescript
// apps/web/src/lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchApi<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
```

**Step 2: Create MetricCard**

A dark card (`bg-bg-card`) that shows:
- Label (small, text-secondary)
- Value (large, font-heading, bold)
- Optional trend indicator (up/down arrow + percentage)

No visible borders. Subtle shadow. Generous padding.

**Step 3: Create ScoreRing**

SVG circular progress indicator for recovery score. Color changes based on value (green > 70, yellow 40-70, red < 40).

**Step 4: Create Gauge**

For Body Battery. Horizontal bar with gradient fill.

**Step 5: Create TrendChart**

Recharts `AreaChart` wrapper with custom styling:
- Gradient fill under the line
- Custom colors from our palette
- Clean axis labels
- No grid lines (minimal look)

**Step 6: Commit**

```bash
git commit -m "feat(web): add shared UI components (MetricCard, ScoreRing, Gauge, TrendChart)"
```

---

## Phase 8: Frontend — Dashboard Pages

### Task 18: Daily Overview Page

**Files:**
- Create: `apps/web/src/app/(dashboard)/page.tsx`
- Create: `apps/web/src/components/dashboard/recovery-score.tsx`
- Create: `apps/web/src/components/dashboard/today-summary.tsx`
- Create: `apps/web/src/components/dashboard/latest-activity.tsx`
- Create: `apps/web/src/components/dashboard/macro-split.tsx`

**Step 1: Fetch data from `/api/dashboard/today`**

**Step 2: Build layout**

```
┌──────────────────────────────────────────┐
│  Recovery Score (big ring)  │  Body Battery │
│  with number + label        │  gauge        │
├─────────┬──────────┬────────┼──────────────┤
│  Sleep  │  Stress  │  Steps │  Calories    │
│  card   │  card    │  card  │  card        │
├─────────┴──────────┴────────┴──────────────┤
│  Latest Activity                            │
│  (type icon, name, duration, HR, TSS)       │
├─────────────────────────────────────────────┤
│  Macro Split (P/C/F donut or bars)          │
└─────────────────────────────────────────────┘
```

Use asymmetric sizing: recovery score takes ~40% width, other metrics fill. Bold numbers, subtle labels.

**Step 3: Style with design system colors**

**Step 4: Commit**

```bash
git commit -m "feat(web): add daily overview dashboard page"
```

---

### Task 19: Performance Page

**Files:**
- Create: `apps/web/src/app/(dashboard)/performance/page.tsx`
- Create: `apps/web/src/components/performance/pmc-chart.tsx`
- Create: `apps/web/src/components/performance/activity-calendar.tsx`
- Create: `apps/web/src/components/performance/load-distribution.tsx`

**Step 1: PMC Chart (main feature)**

Full-width Recharts `ComposedChart` with:
- CTL line (blue, fitness)
- ATL line (orange/red, fatigue)
- TSB area fill (green when positive, red when negative)
- Time range selector: 30d / 90d / 6m / 1y / All
- Tooltip with all values

**Step 2: Activity calendar**

GitHub-contribution-style heatmap grid, colored by daily TSS intensity.

**Step 3: Load distribution**

Stacked bar chart: cardio TSS vs strength TSS per week.

**Step 4: VO2max trend line**

Simple line chart.

**Step 5: Commit**

```bash
git commit -m "feat(web): add performance page with PMC chart and activity calendar"
```

---

### Task 20: Sleep Page

**Files:**
- Create: `apps/web/src/app/(dashboard)/sleep/page.tsx`
- Create: `apps/web/src/components/sleep/sleep-architecture.tsx`
- Create: `apps/web/src/components/sleep/hrv-trend.tsx`
- Create: `apps/web/src/components/sleep/sleep-score-trend.tsx`

**Step 1: Sleep architecture chart**

Stacked horizontal bars per night: deep (dark blue), light (light blue), REM (purple), awake (red).
Last 14 nights.

**Step 2: HRV nocturno trend**

Line chart, last 30 days.

**Step 3: Sleep score trend**

Line chart with color zones (green > 80, yellow 60-80, red < 60).

**Step 4: FC during sleep + SpO2**

Small metric cards with sparklines.

**Step 5: Commit**

```bash
git commit -m "feat(web): add sleep analysis page"
```

---

### Task 21: Nutrition Page

**Files:**
- Create: `apps/web/src/app/(dashboard)/nutrition/page.tsx`
- Create: `apps/web/src/components/nutrition/calorie-trend.tsx`
- Create: `apps/web/src/components/nutrition/macro-donut.tsx`
- Create: `apps/web/src/components/nutrition/protein-target.tsx`

**Step 1: Daily calorie bar chart** (last 14 days, with target line)

**Step 2: Macro donut** (today's P/C/F with grams and percentages)

**Step 3: Protein per kg trend** (needs weight from daily_summaries or settings)

**Step 4: Calorie vs TSS overlay** (dual-axis chart showing correlation)

**Step 5: Commit**

```bash
git commit -m "feat(web): add nutrition tracking page"
```

---

### Task 22: Body & Health Page

**Files:**
- Create: `apps/web/src/app/(dashboard)/body/page.tsx`
- Create: `apps/web/src/components/body/resting-hr-trend.tsx`
- Create: `apps/web/src/components/body/stress-heatmap.tsx`
- Create: `apps/web/src/components/body/body-battery-pattern.tsx`

**Step 1: Resting HR trend** (line chart, 30 days)

**Step 2: Stress heatmap** (7-day weekly pattern, hours as columns, days as rows)

**Step 3: Body Battery weekly pattern** (high/low range per day)

**Step 4: Weight trend** (if available)

**Step 5: Hydration bars** (daily ml)

**Step 6: Commit**

```bash
git commit -m "feat(web): add body and health metrics page"
```

---

### Task 23: Activity Detail Page

**Files:**
- Create: `apps/web/src/app/(dashboard)/activities/[id]/page.tsx`
- Create: `apps/web/src/components/activity/activity-header.tsx`
- Create: `apps/web/src/components/activity/activity-metrics.tsx`

**Step 1: Dynamic route `/activities/[id]`**

Fetch activity by ID from `/api/activities/{id}`.

**Step 2: Header** — activity type icon, name, date, duration.

**Step 3: Metrics grid** — HR (avg/max), power (if available), calories, TSS, training effect, elevation, distance.

**Step 4: If strength activity** — table with exercise/sets/reps/weight.

**Step 5: Commit**

```bash
git commit -m "feat(web): add activity detail page"
```

---

## Phase 9: Polish & Integration

### Task 24: End-to-End Integration Test

**Step 1: Start Docker (PostgreSQL)**
**Step 2: Run Alembic migrations**
**Step 3: Start FastAPI backend**
**Step 4: Trigger manual sync with real Garmin credentials**
**Step 5: Start Next.js frontend**
**Step 6: Verify all pages load with real data**
**Step 7: Fix any field mapping issues between Garmin API and our models**
**Step 8: Commit any fixes**

```bash
git commit -m "fix(sync): adjust Garmin API field mappings from integration testing"
```

---

### Task 25: Dev Experience

**Files:**
- Create: `Makefile` or `scripts/dev.sh`
- Create: `apps/web/.prettierrc`
- Create: `README.md`

**Step 1: Create dev scripts**

```makefile
# Makefile
dev-db:
	docker compose up -d

dev-api:
	cd apps/sync && uv run uvicorn app.main:app --reload --port 8000

dev-web:
	cd apps/web && pnpm dev

dev: dev-db dev-api dev-web

migrate:
	cd apps/sync && uv run alembic upgrade head

sync:
	curl -X POST http://localhost:8000/api/sync/trigger

lint:
	cd apps/sync && uv run ruff check .
	cd apps/web && pnpm lint

format:
	cd apps/sync && uv run ruff format .
	cd apps/web && pnpm prettier --write "src/**/*.{ts,tsx}"
```

**Step 2: Commit**

```bash
git commit -m "chore: add Makefile and dev scripts"
```

---

## Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| 1 | 1-3 | Infrastructure: Docker, FastAPI, Next.js scaffolding |
| 2 | 4-5 | Database: models + migrations |
| 3 | 6-7 | Garmin sync service |
| 4 | 8-10 | TSS/ATL/CTL/TSB calculations |
| 5 | 11-13 | API endpoints |
| 6 | 14 | Scheduler (cron) |
| 7 | 15 | MyFitnessPal integration |
| 8 | 16-17 | Frontend foundation (layout, shared components) |
| 9 | 18-23 | Frontend pages (6 dashboard pages) |
| 10 | 24-25 | Integration testing + dev experience |
