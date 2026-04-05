import { toLocalDateStr } from "./date-utils";

// ── Plan dashboard types ──

export interface StripMetric {
  label: string;
  value: string;
  secondary_value: string | null;
  unit: string;
  target: string | null;
  pct: number | null;
  trend: string | null;
}

export interface PillarKPI {
  label: string;
  value: string;
  unit: string;
  target: string | null;
  status: string | null;
  spark: number[];
}

export interface PillarDriver {
  label: string;
  value: string;
  unit: string;
}

export interface PillarData {
  id: string;
  name: string;
  color: string;
  collapsed_kpis: PillarKPI[];
  expanded_kpis: PillarKPI[];
  drivers: PillarDriver[];
}

export interface SyncSourceStatus {
  source: string;
  last_date: string | null;
  ok: boolean;
}

export interface PlanDailyData {
  date: string;
  strip: StripMetric[];
  pillars: PillarData[];
  sync_status: SyncSourceStatus[];
}

export function emptyPlanDailyData(): PlanDailyData {
  return {
    date: toLocalDateStr(new Date()),
    strip: [],
    pillars: [],
    sync_status: [],
  };
}

// ── Aerobico tab types ──

export interface PMCDataPoint {
  date: string;
  ctl: number | null;
  atl: number | null;
  tsb: number | null;
  tss_day: number | null;
}

export interface CalendarPlannedWorkout {
  tp_workout_id: string;
  date: string;
  title: string | null;
  workout_type: string | null;
  description: string | null;
  duration_sec_planned: number | null;
  tss_planned: number | null;
  distance_m_planned: number | null;
}

export interface CalendarCompletedWorkout {
  tp_workout_id: string;
  date: string;
  title: string | null;
  workout_type: string | null;
  description: string | null;
  tss: number | null;
  distance_m: number | null;
  duration_sec: number | null;
}

export interface CalendarData {
  planned: CalendarPlannedWorkout[];
  completed: CalendarCompletedWorkout[];
}

export interface WorkoutDetailsJSON {
  timeInHeartRateZones?: {
    timeInZones: { seconds: number; minimum: number; maximum: number; label: string }[];
    threshold?: number;
  };
  timeInSpeedZones?: {
    timeInZones: { seconds: number; minimum: number; maximum: number; label: string }[];
    threshold?: number;
  };
  timeInPowerZones?: {
    timeInZones: { seconds: number; minimum: number; maximum: number; label: string }[];
    threshold?: number;
  };
  meanMaxSpeedsByDistance?: {
    meanMaxes: { label: string; value: number | null }[];
  };
  meanMaxSpeeds?: {
    meanMaxes: { label: string; value: number | null }[];
  };
  meanMaxHeartRates?: {
    meanMaxes: { label: string; value: number | null }[];
  };
  meanMaxPowers?: {
    meanMaxes: { label: string; value: number | null }[];
  };
}

export interface WorkoutStructureStep {
  type: "step" | "repetition";
  name?: string;
  intensityClass?: "warmUp" | "active" | "coolDown";
  length: { unit: string; value: number };
  steps?: WorkoutStructureStep[];
  targets?: { minValue: number; maxValue: number }[];
  begin?: number;
  end?: number;
}

export interface WorkoutStructure {
  polyline: [number, number][];
  structure: WorkoutStructureStep[];
  primaryIntensityMetric?: string;
}

export interface CompletedWorkoutDetail {
  tp_workout_id: string;
  date: string;
  title: string | null;
  workout_type: string | null;
  description: string | null;
  duration_sec: number | null;
  distance_m: number | null;
  tss: number | null;
  intensity_factor: number | null;
  avg_hr: number | null;
  max_hr: number | null;
  avg_power: number | null;
  calories: number | null;
  elevation_gain_m: number | null;
  workout_details_json: WorkoutDetailsJSON | null;
}

export interface PlannedWorkoutDetail {
  tp_workout_id: string;
  date: string;
  title: string | null;
  workout_type: string | null;
  description: string | null;
  duration_sec_planned: number | null;
  distance_m_planned: number | null;
  tss_planned: number | null;
  structure_json: WorkoutStructure | null;
}

export interface WorkoutWithPlanned {
  workout: CompletedWorkoutDetail | PlannedWorkoutDetail;
  planned: PlannedWorkoutDetail | null;
  completed: CompletedWorkoutDetail | null;
}

export interface WeeklyVolume {
  week_start: string;
  km: number;
  elevation_m: number;
}

export interface WeeklyHRZones {
  week_start: string;
  zone1_sec: number;
  zone2_sec: number;
  zone3_sec: number;
  zone4_sec: number;
  zone5_sec: number;
}

export type HRZonesData = WeeklyHRZones[];

// ── Nutrición tab types ──

export interface NutritionDay {
  id: number;
  date: string;
  calories: number | null;
  protein_g: number | null;
  carbs_g: number | null;
  fat_g: number | null;
  fiber_g: number | null;
  sodium_mg: number | null;
  calories_goal: number | null;
  protein_goal_g: number | null;
  alcohol_drinks: number | null;
  calories_target_adaptive: number | null;
}

export interface BodyCompositionDay {
  date: string;
  weight_kg: number | null;
  body_fat_pct: number | null;
}
