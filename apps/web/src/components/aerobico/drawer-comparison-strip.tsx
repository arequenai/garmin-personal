"use client";

import type { CompletedWorkoutDetail, PlannedWorkoutDetail } from "@/lib/types";

function formatDuration(sec: number | null): string {
  if (!sec) return "—";
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  return h > 0 ? `${h}h${m.toString().padStart(2, "0")}` : `${m}m`;
}

function deltaColor(planned: number, actual: number): string {
  const pct = Math.abs((actual - planned) / planned);
  if (pct <= 0.1) return "#00d68f";
  if (pct <= 0.25) return "#f59e0b";
  return "#ef4444";
}

interface ComparisonItem {
  label: string;
  planned: string;
  actual: string;
  delta: string;
  color: string;
}

interface DrawerComparisonStripProps {
  completed: CompletedWorkoutDetail;
  planned: PlannedWorkoutDetail;
}

export function DrawerComparisonStrip({ completed, planned }: DrawerComparisonStripProps) {
  const items: ComparisonItem[] = [];

  if (planned.duration_sec_planned != null && completed.duration_sec != null) {
    const diff = completed.duration_sec - planned.duration_sec_planned;
    const m = Math.round(diff / 60);
    items.push({
      label: "Duration",
      planned: formatDuration(planned.duration_sec_planned),
      actual: formatDuration(completed.duration_sec),
      delta: `${m >= 0 ? "+" : ""}${m}min`,
      color: deltaColor(planned.duration_sec_planned, completed.duration_sec),
    });
  }

  if (planned.distance_m_planned != null && completed.distance_m != null) {
    const plannedKm = planned.distance_m_planned / 1000;
    const actualKm = completed.distance_m / 1000;
    const diffKm = actualKm - plannedKm;
    items.push({
      label: "Distance",
      planned: `${plannedKm.toFixed(1)} km`,
      actual: `${actualKm.toFixed(1)} km`,
      delta: `${diffKm >= 0 ? "+" : ""}${diffKm.toFixed(1)} km`,
      color: deltaColor(planned.distance_m_planned, completed.distance_m),
    });
  }

  if (planned.tss_planned != null && completed.tss != null) {
    const diff = Math.round(completed.tss - planned.tss_planned);
    items.push({
      label: "TSS",
      planned: String(Math.round(planned.tss_planned)),
      actual: String(Math.round(completed.tss)),
      delta: `${diff >= 0 ? "+" : ""}${diff}`,
      color: deltaColor(planned.tss_planned, completed.tss),
    });
  }

  if (items.length === 0) return null;

  return (
    <div
      className="flex items-center gap-6 px-4 py-2"
      style={{
        borderBottom: "1px solid rgba(255,255,255,0.04)",
        background: "rgba(255,255,255,0.02)",
      }}
    >
      <span className="text-[10px] font-semibold uppercase tracking-wider text-whoop-text-muted">
        Plan vs Actual
      </span>
      {items.map((item) => (
        <div key={item.label} className="flex items-center gap-2 text-[11px]">
          <span className="text-whoop-text-muted">{item.label}:</span>
          <span className="text-whoop-text-secondary">{item.planned}</span>
          <span className="text-whoop-text-muted">&rarr;</span>
          <span className="text-whoop-text">{item.actual}</span>
          <span className="font-medium" style={{ color: item.color }}>
            ({item.delta})
          </span>
        </div>
      ))}
    </div>
  );
}
