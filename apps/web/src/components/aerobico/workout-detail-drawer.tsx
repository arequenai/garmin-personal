"use client";

import { X } from "lucide-react";
import type {
  CompletedWorkoutDetail,
  PlannedWorkoutDetail,
  WorkoutWithPlanned,
} from "@/lib/types";
import { useWorkoutDetail } from "@/lib/hooks/use-workout-detail";
import { DrawerCompletedBody } from "./drawer-completed-body";
import { DrawerPlannedBody } from "./drawer-planned-body";
import { DrawerComparisonStrip } from "./drawer-comparison-strip";
import { DrawerCharts } from "./drawer-charts";
import { DrawerStructureViz } from "./drawer-structure-viz";

const WORKOUT_COLORS: Record<string, string> = {
  run: "#00d68f",
  bike: "#4da6ff",
  swim: "#00c4b4",
  strength: "#a855f7",
  hike: "#f59e0b",
};
const DEFAULT_COLOR = "#6b7280";

function getColor(type: string | null): string {
  if (!type) return DEFAULT_COLOR;
  const key = type.toLowerCase();
  for (const [k, v] of Object.entries(WORKOUT_COLORS)) {
    if (key.includes(k)) return v;
  }
  return DEFAULT_COLOR;
}

function isCompleted(
  w: CompletedWorkoutDetail | PlannedWorkoutDetail,
): w is CompletedWorkoutDetail {
  return "duration_sec" in w;
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

interface WorkoutDetailDrawerProps {
  selection: { id: string; type: "completed" | "planned" } | null;
  onClose: () => void;
}

export function WorkoutDetailDrawer({ selection, onClose }: WorkoutDetailDrawerProps) {
  const { data, loading, error } = useWorkoutDetail(selection);
  const isOpen = selection !== null;

  return (
    <div
      className="overflow-hidden transition-all duration-300 ease-out"
      style={{ maxHeight: isOpen ? "600px" : "0px" }}
    >
      {isOpen && (
        <div className="mt-4 rounded-xl border border-whoop-border bg-whoop-card">
          {loading && (
            <div className="p-4">
              <div className="h-[200px] animate-pulse rounded bg-whoop-surface" />
            </div>
          )}

          {error && (
            <div className="flex items-center justify-center p-8">
              <p className="text-xs text-whoop-text-muted">Could not load workout details</p>
            </div>
          )}

          {data && <DrawerContent data={data} onClose={onClose} />}
        </div>
      )}
    </div>
  );
}

function DrawerContent({ data, onClose }: { data: WorkoutWithPlanned; onClose: () => void }) {
  const workout = data.workout;
  const color = getColor(workout.workout_type);
  const completed = isCompleted(workout);
  const title = workout.title || (completed ? "Workout" : "Planned");
  const typeBadge = workout.workout_type || "Workout";

  return (
    <>
      {/* Header bar */}
      <div
        className="flex items-center justify-between px-4 py-3"
        style={{
          borderBottom: "1px solid rgba(255,255,255,0.06)",
          borderLeft: `3px solid ${color}`,
          background: `linear-gradient(90deg, ${color}10, transparent)`,
        }}
      >
        <div className="flex items-center gap-3">
          <span className="text-sm font-semibold text-whoop-text">{title}</span>
          <span className="text-xs text-whoop-text-muted">
            {typeBadge} &bull; {formatDate(workout.date)}
          </span>
          {!completed && (
            <span className="rounded border border-whoop-border px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider text-whoop-text-muted"
              style={{ borderStyle: "dashed" }}
            >
              Planned
            </span>
          )}
        </div>
        <button
          onClick={onClose}
          className="rounded p-1 text-whoop-text-muted hover:bg-whoop-surface hover:text-whoop-text transition-colors"
        >
          <X size={16} />
        </button>
      </div>

      {/* Comparison strip */}
      {completed && data.planned && (
        <DrawerComparisonStrip
          completed={workout as CompletedWorkoutDetail}
          planned={data.planned}
        />
      )}
      {!completed && data.completed && (
        <DrawerComparisonStrip
          completed={data.completed}
          planned={workout as PlannedWorkoutDetail}
        />
      )}

      {/* Body */}
      {completed ? (
        <DrawerCompletedBody workout={workout as CompletedWorkoutDetail} color={color} />
      ) : (
        <DrawerPlannedBody workout={workout as PlannedWorkoutDetail} color={color} />
      )}

      {/* Charts / Structure */}
      {completed && (
        <DrawerCharts workout={workout as CompletedWorkoutDetail} />
      )}
      {!completed && (workout as PlannedWorkoutDetail).structure_json && (
        <DrawerStructureViz structure={(workout as PlannedWorkoutDetail).structure_json!} />
      )}
    </>
  );
}
