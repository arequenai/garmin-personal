"use client";

import type { PlannedWorkoutDetail } from "@/lib/types";

function formatDuration(sec: number | null): string {
  if (!sec) return "—";
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  return h > 0 ? `${h}h ${m.toString().padStart(2, "0")}m` : `${m}m`;
}

function formatKm(meters: number | null): string {
  if (!meters || meters < 100) return "—";
  return `${(meters / 1000).toFixed(1)} km`;
}

interface DrawerPlannedBodyProps {
  workout: PlannedWorkoutDetail;
  color: string;
}

export function DrawerPlannedBody({ workout, color }: DrawerPlannedBodyProps) {
  return (
    <div className="flex" style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
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

      <div className="w-[200px] shrink-0 space-y-1.5 p-4">
        <div className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-whoop-text-muted">
          Planned Targets
        </div>
        <div className="flex justify-between text-[11px]">
          <span className="text-whoop-text-muted">Duration</span>
          <span className="italic text-whoop-text-secondary">{formatDuration(workout.duration_sec_planned)}</span>
        </div>
        <div className="flex justify-between text-[11px]">
          <span className="text-whoop-text-muted">Distance</span>
          <span className="italic text-whoop-text-secondary">{formatKm(workout.distance_m_planned)}</span>
        </div>
        <div className="flex justify-between text-[11px]">
          <span className="text-whoop-text-muted">TSS</span>
          <span className="italic text-whoop-text-secondary">
            {workout.tss_planned != null ? String(Math.round(workout.tss_planned)) : "—"}
          </span>
        </div>
      </div>
    </div>
  );
}
