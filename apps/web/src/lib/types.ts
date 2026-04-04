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

export interface PlanDailyData {
  date: string;
  strip: StripMetric[];
  pillars: PillarData[];
}

export function emptyPlanDailyData(): PlanDailyData {
  return {
    date: new Date().toISOString().split("T")[0],
    strip: [],
    pillars: [],
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
  date: string;
  title: string | null;
  workout_type: string | null;
  duration_sec_planned: number | null;
  tss_planned: number | null;
  distance_m_planned: number | null;
}

export interface CalendarCompletedWorkout {
  date: string;
  title: string | null;
  workout_type: string | null;
  tss: number | null;
  distance_m: number | null;
  duration_sec: number | null;
}

export interface CalendarData {
  planned: CalendarPlannedWorkout[];
  completed: CalendarCompletedWorkout[];
}

export interface WeeklyVolume {
  week_start: string;
  km: number;
  elevation_m: number;
}

export interface HRZonesData {
  zone1_sec: number;
  zone2_sec: number;
  zone3_sec: number;
  zone4_sec: number;
  zone5_sec: number;
}
