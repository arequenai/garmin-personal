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
