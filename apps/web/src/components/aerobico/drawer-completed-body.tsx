"use client";

import type { CompletedWorkoutDetail } from "@/lib/types";

function formatDuration(sec: number | null): string {
  if (!sec) return "—";
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  return h > 0 ? `${h}h ${m.toString().padStart(2, "0")}m` : `${m}m`;
}

function formatPace(distM: number | null, sec: number | null): string {
  if (!distM || !sec || distM < 100) return "—";
  const paceSecPerKm = sec / (distM / 1000);
  const min = Math.floor(paceSecPerKm / 60);
  const s = Math.round(paceSecPerKm % 60);
  return `${min}:${s.toString().padStart(2, "0")} /km`;
}

function formatKm(meters: number | null): string {
  if (!meters || meters < 100) return "—";
  return `${(meters / 1000).toFixed(1)} km`;
}

function MetricRow({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="flex justify-between text-[11px]">
      <span className="text-whoop-text-muted">{label}</span>
      <span className="font-medium" style={{ color: color || "var(--whoop-text)" }}>{value}</span>
    </div>
  );
}

interface DrawerCompletedBodyProps {
  workout: CompletedWorkoutDetail;
  color: string;
}

export function DrawerCompletedBody({ workout, color }: DrawerCompletedBodyProps) {
  return (
    <div className="flex" style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
      {/* Left: Coach Notes */}
      <div className="flex-1 p-4" style={{ borderRight: "1px solid rgba(255,255,255,0.04)" }}>
        <div className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider" style={{ color }}>
          Coach Notes
        </div>
        {workout.description ? (
          <div className="whitespace-pre-line text-xs leading-relaxed text-whoop-text-secondary">
            {workout.description}
          </div>
        ) : (
          <div className="text-xs text-whoop-text-muted italic">No notes</div>
        )}
      </div>

      {/* Right: Key Metrics */}
      <div className="w-[200px] shrink-0 space-y-1.5 p-4">
        <MetricRow label="Distance" value={formatKm(workout.distance_m)} />
        <MetricRow label="Duration" value={formatDuration(workout.duration_sec)} />
        <MetricRow label="Avg Pace" value={formatPace(workout.distance_m, workout.duration_sec)} />
        <MetricRow label="TSS" value={workout.tss != null ? String(Math.round(workout.tss)) : "—"} color="#4da6ff" />
        <MetricRow label="IF" value={workout.intensity_factor != null ? workout.intensity_factor.toFixed(2) : "—"} />
        <MetricRow label="Avg HR" value={workout.avg_hr != null ? `${workout.avg_hr} bpm` : "—"} color="#ef4444" />
        <MetricRow label="Max HR" value={workout.max_hr != null ? `${workout.max_hr} bpm` : "—"} color="#ef4444" />
        {workout.elevation_gain_m != null && (
          <MetricRow label="Elevation" value={`${Math.round(workout.elevation_gain_m)}m`} />
        )}
        <MetricRow label="Calories" value={workout.calories != null ? workout.calories.toLocaleString() : "—"} />
      </div>
    </div>
  );
}
