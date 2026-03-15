// ── API response types aligned with backend Pydantic schemas ──

export interface DailySummary {
  id: number;
  date: string;
  steps: number | null;
  calories_total: number | null;
  calories_active: number | null;
  distance_m: number | null;
  floors: number | null;
  avg_hr: number | null;
  resting_hr: number | null;
  max_hr: number | null;
  min_hr: number | null;
  stress_avg: number | null;
  stress_max: number | null;
  body_battery_high: number | null;
  body_battery_low: number | null;
  spo2_avg: number | null;
  respiration_avg: number | null;
  hydration_ml: number | null;
}

export interface SleepSession {
  id: number;
  date: string;
  sleep_start: string | null;
  sleep_end: string | null;
  total_sleep_min: number | null;
  deep_min: number | null;
  light_min: number | null;
  rem_min: number | null;
  awake_min: number | null;
  avg_hr_sleep: number | null;
  avg_hrv: number | null;
  avg_spo2_sleep: number | null;
  sleep_score: number | null;
}

export interface Activity {
  id: number;
  garmin_id: string;
  date: string;
  type: string | null;
  name: string | null;
  duration_sec: number | null;
  distance_m: number | null;
  calories: number | null;
  avg_hr: number | null;
  max_hr: number | null;
  avg_power: number | null;
  max_power: number | null;
  training_effect_aerobic: number | null;
  training_effect_anaerobic: number | null;
  vo2max_estimate: number | null;
  elevation_gain: number | null;
  tss: number | null;
}

export interface NutritionDaily {
  id: number;
  date: string;
  calories: number | null;
  protein_g: number | null;
  carbs_g: number | null;
  fat_g: number | null;
  fiber_g: number | null;
  sodium_mg: number | null;
}

export interface PerformanceMetric {
  id: number;
  date: string;
  tss: number | null;
  atl: number | null;
  ctl: number | null;
  tsb: number | null;
  training_load_7d: number | null;
  training_load_28d: number | null;
  recovery_score: number | null;
  vo2max: number | null;
  endurance_score: number | null;
  hill_score: number | null;
  fitness_age: number | null;
  category_scores: Record<string, number> | null;
}

export interface DashboardData {
  date: string;
  daily_summary: DailySummary | null;
  sleep: SleepSession | null;
  latest_activity: Activity | null;
  nutrition: NutritionDaily | null;
  performance: PerformanceMetric | null;
}

// ── Overview types ──

export interface KeyIndicator {
  label: string;
  value: string;
  unit: string;
  trend_pct: number;
  spark: number[];
}

export interface KPI {
  label: string;
  value: string;
  unit: string;
  trend_pct: number;
}

export interface OverviewDriver {
  label: string;
  value: string;
  unit: string;
  trend_pct: number;
}

export interface OverviewCategory {
  score: number | null;
  key_indicator: KeyIndicator | null;
  kpis: KPI[];
  drivers: OverviewDriver[];
}

export interface DailyMetric {
  label: string;
  value: string;
  unit: string;
  target: string;
  pct: number;
}

export interface DailySection {
  id: string;
  label: string;
  icon: string;
  color: string;
  metrics: DailyMetric[];
}

export interface OverviewData {
  date: string;
  categories: Record<string, OverviewCategory>;
  daily_sections: DailySection[];
}

export interface UserGoal {
  metric_key: string;
  target_value: number;
  target_unit: string;
  category: string;
}

const EMPTY_CATEGORY: OverviewCategory = { score: null, key_indicator: null, kpis: [], drivers: [] };

export function emptyOverviewData(): OverviewData {
  return {
    date: new Date().toISOString().split("T")[0],
    categories: {
      running: EMPTY_CATEGORY,
      strength: EMPTY_CATEGORY,
      recovery: EMPTY_CATEGORY,
      sleep: EMPTY_CATEGORY,
      body: EMPTY_CATEGORY,
      glucose: EMPTY_CATEGORY,
    },
    daily_sections: [],
  };
}
