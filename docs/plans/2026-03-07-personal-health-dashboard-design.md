# Personal Health & Performance Dashboard — Design Doc

## Vision

Webapp personal estilo Whoop/Bevel para analizar datos de salud, deporte, nutricion, sueno y recuperacion. Fuentes: Garmin Connect (principal) y MyFitnessPal (nutricion). Logica de ATL/CTL/TSB calculada internamente con datos de Garmin.

## Arquitectura

Monorepo fullstack:

```
garmin-personal/
├── apps/
│   ├── web/          # Next.js 14+ (App Router) + Tailwind — dashboards
│   └── sync/         # Python FastAPI — sincronizacion + API de datos
├── database/         # PostgreSQL (migraciones, seeds, docker-compose)
```

- **Next.js** sirve el frontend con dashboards
- **FastAPI** expone la API REST que Next.js consume y ejecuta la sincronizacion con Garmin + MFP
- **PostgreSQL** local con Docker
- Calculos de ATL/CTL/TSB en Python
- Usuario unico, sin auth

## Modelo de datos

### users
| Campo | Tipo |
|-------|------|
| id | PK |
| garmin_email | string |
| garmin_password | string (encriptado) |
| mfp_credentials | string (encriptado) |
| hr_max | int |
| hr_rest | int |
| hr_threshold | int |
| created_at | timestamp |

### daily_summaries
| Campo | Tipo |
|-------|------|
| id | PK |
| date | date (unique) |
| steps | int |
| calories_total | int |
| calories_active | int |
| distance_m | float |
| floors | int |
| avg_hr | int |
| resting_hr | int |
| max_hr | int |
| min_hr | int |
| stress_avg | int |
| stress_max | int |
| body_battery_high | int |
| body_battery_low | int |
| spo2_avg | float |
| respiration_avg | float |
| hydration_ml | int |

### sleep_sessions
| Campo | Tipo |
|-------|------|
| id | PK |
| date | date (unique) |
| sleep_start | timestamp |
| sleep_end | timestamp |
| total_sleep_min | int |
| deep_min | int |
| light_min | int |
| rem_min | int |
| awake_min | int |
| avg_hr_sleep | int |
| avg_hrv | float |
| avg_spo2_sleep | float |
| sleep_score | int |

### activities
| Campo | Tipo |
|-------|------|
| id | PK |
| garmin_id | string (unique) |
| date | date |
| type | string |
| name | string |
| duration_sec | int |
| distance_m | float |
| calories | int |
| avg_hr | int |
| max_hr | int |
| avg_power | float |
| max_power | float |
| training_effect_aerobic | float |
| training_effect_anaerobic | float |
| vo2max_estimate | float |
| elevation_gain | float |
| tss | float (calculado) |

### strength_sessions
| Campo | Tipo |
|-------|------|
| id | PK |
| activity_id | FK -> activities |
| exercise_name | string |
| sets | int |
| reps | int |
| weight_kg | float |
| tonnage | float |

### nutrition_daily
| Campo | Tipo |
|-------|------|
| id | PK |
| date | date (unique) |
| calories | int |
| protein_g | float |
| carbs_g | float |
| fat_g | float |
| fiber_g | float |
| sodium_mg | float |

### performance_metrics
| Campo | Tipo |
|-------|------|
| id | PK |
| date | date (unique) |
| tss | float |
| atl | float |
| ctl | float |
| tsb | float |
| training_load_7d | float |
| training_load_28d | float |
| recovery_score | float |

## Sincronizacion

- Cron diario (APScheduler) a las 5:00 AM
- Login en Garmin Connect con `garminconnect`, descarga datos del dia anterior
- Extraccion de MyFitnessPal para nutricion
- Calculo de TSS por actividad:
  - Cardio con FC: `TSS = (duracion * IF^2 * 100) / 3600` donde IF = FC_media / FC_umbral
  - Cardio con potencia: TSS estandar
  - Fuerza: estimado con duracion * training effect
- Actualizacion de ATL/CTL/TSB:
  - CTL = media exponencial de TSS a 42 dias
  - ATL = media exponencial de TSS a 7 dias
  - TSB = CTL - ATL
- Endpoint `/api/sync/trigger` para forzar sincronizacion manual

## API (FastAPI)

```
GET  /api/dashboard/today          # resumen del dia
GET  /api/activities?from=&to=     # lista de actividades
GET  /api/sleep?from=&to=          # datos de sueno
GET  /api/nutrition?from=&to=      # datos de nutricion
GET  /api/performance?from=&to=    # ATL/CTL/TSB historico
GET  /api/daily?from=&to=          # resumenes diarios
POST /api/sync/trigger             # forzar sincronizacion
GET  /api/settings                 # config usuario
PUT  /api/settings                 # actualizar config
```

## Dashboards

### Daily Overview (pagina principal)
- Score de recuperacion (HRV + sueno + TSB) con indicador visual tipo semaforo
- Body Battery actual (gauge)
- Resumen rapido: sueno, estres, pasos, calorias
- Ultima actividad con metricas clave
- Macro split del dia (proteina/carbs/grasa)

### Performance — Training Load
- Grafico PMC (ATL/CTL/TSB) estilo TrainingPeaks
- Calendario de actividades con intensidad por color
- Distribucion de carga semanal (cardio vs fuerza)
- TSS por actividad (7/30/90 dias)
- VO2max trend

### Sleep
- Arquitectura del sueno (deep/light/REM/awake) barras apiladas
- HRV nocturno trend
- FC durante sueno
- Sleep score trend
- SpO2 nocturno

### Nutrition
- Calorias diarias vs objetivo
- Macro breakdown (donut chart)
- Proteina/kg de peso corporal
- Correlacion calorias vs rendimiento (overlay con TSS)

### Body & Health
- Peso trend
- FC reposo trend
- Estres diario (heatmap)
- Body Battery patron semanal
- Hidratacion

### Activity Detail
- Metricas completas por actividad
- Graficos de FC/potencia
- Splits

## Identidad visual

- **Tema oscuro** por defecto
- Background: `#0a0a0f`, cards: `#12121a`
- Texto primario: `#e8e8ed`, secundario: `#6b6b7b`
- Recovery/green: `#22c55e`, Strain/orange: `#f97316`, Sleep/blue: `#6366f1`, Alert/red: `#ef4444`
- Tipografia: Inter (body), Space Grotesk o Sora (headings)
- Sin bordes visibles en cards, diferencias sutiles de fondo + sombras suaves
- Graficos con gradientes sutiles, paleta custom en Recharts
- Animaciones minimas (transiciones, conteo de numeros)
- Espaciado generoso, datos grandes y bold como focal point
- Asimetria intencional en layouts
- Evitar: gradientes neon, glassmorphism, cards genericas, paletas por defecto

## Stack tecnico

### Frontend
- Next.js 14+ (App Router) + TypeScript
- Tailwind CSS
- Recharts (graficos)
- Lucide icons
- date-fns

### Backend
- FastAPI + Uvicorn
- garminconnect (libreria Python)
- myfitnesspal (o scraping)
- SQLAlchemy (ORM)
- Alembic (migraciones)
- APScheduler (cron)
- NumPy (calculos)

### Infra
- PostgreSQL 16 (Docker)
- docker-compose.yml

### Dev tooling
- pnpm (frontend)
- uv o poetry (Python)
- ESLint + Prettier (frontend)
- Ruff (Python)
- Husky + lint-staged (pre-commit hooks)
