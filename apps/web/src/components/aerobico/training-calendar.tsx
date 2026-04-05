"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import type { CalendarPlannedWorkout, CalendarCompletedWorkout } from "@/lib/types";
import { useAerobicCalendar } from "@/lib/hooks/use-aerobic-calendar";
import { toLocalDateStr } from "@/lib/date-utils";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

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

function formatDuration(sec: number | null): string {
  if (!sec) return "";
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  return h > 0 ? `${h}h${m.toString().padStart(2, "0")}` : `${m}m`;
}

function formatKm(meters: number | null): string {
  if (!meters || meters < 100) return "";
  return `${(meters / 1000).toFixed(1)}k`;
}

function formatDurationLong(sec: number | null): string {
  if (!sec) return "";
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

function formatKmLong(meters: number | null): string {
  if (!meters || meters < 100) return "";
  return `${(meters / 1000).toFixed(2)} km`;
}

function WorkoutBlock({ workout, planned }: {
  workout: CalendarCompletedWorkout | CalendarPlannedWorkout;
  planned?: boolean;
}) {
  const [hovered, setHovered] = useState(false);
  const type = workout.workout_type;
  const title = workout.title;
  const color = getColor(type);

  const duration = planned
    ? formatDuration((workout as CalendarPlannedWorkout).duration_sec_planned)
    : formatDuration((workout as CalendarCompletedWorkout).duration_sec);
  const distance = planned
    ? formatKm((workout as CalendarPlannedWorkout).distance_m_planned)
    : formatKm((workout as CalendarCompletedWorkout).distance_m);

  // Tooltip detail lines
  const details: string[] = [];
  if (type) details.push(type);
  if (planned) {
    const p = workout as CalendarPlannedWorkout;
    const dur = formatDurationLong(p.duration_sec_planned);
    if (dur) details.push(`Duration: ${dur}`);
    const dist = formatKmLong(p.distance_m_planned);
    if (dist) details.push(`Distance: ${dist}`);
    if (p.tss_planned != null) details.push(`TSS: ${p.tss_planned}`);
  } else {
    const c = workout as CalendarCompletedWorkout;
    const dur = formatDurationLong(c.duration_sec);
    if (dur) details.push(`Duration: ${dur}`);
    const dist = formatKmLong(c.distance_m);
    if (dist) details.push(`Distance: ${dist}`);
    if (c.tss != null) details.push(`TSS: ${Math.round(c.tss)}`);
  }

  return (
    <div
      className="relative"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <div
        className={`cursor-default rounded px-1.5 py-0.5 text-[10px] leading-tight ${
          planned ? "opacity-50 border border-dashed" : ""
        }`}
        style={{
          borderLeft: planned ? undefined : `2px solid ${color}`,
          borderColor: planned ? color : undefined,
          backgroundColor: planned ? "transparent" : `${color}10`,
        }}
      >
        <div className="truncate font-medium text-whoop-text">
          {title || (planned ? "Planned" : "Workout")}
        </div>
        {(duration || distance) && (
          <div className="text-whoop-text-muted">
            {[duration, distance].filter(Boolean).join(" · ")}
          </div>
        )}
      </div>

      {/* Hover tooltip */}
      {hovered && (details.length > 0 || workout.description) && (
        <div className="absolute left-0 bottom-full z-50 mb-1 w-64 max-h-72 overflow-y-auto rounded-lg border border-whoop-border bg-whoop-card p-2.5 shadow-xl">
          <div className="flex items-center gap-1.5 mb-1.5">
            <div className="h-2 w-2 shrink-0 rounded-full" style={{ background: color }} />
            <span className="text-xs font-semibold text-whoop-text truncate">
              {title || (planned ? "Planned" : "Workout")}
            </span>
          </div>
          {planned && (
            <div className="mb-1.5 text-[10px] font-medium uppercase tracking-wider text-whoop-text-muted">
              Planned
            </div>
          )}
          {details.map((line, i) => (
            <div key={i} className="text-[11px] leading-relaxed text-whoop-text-secondary">
              {line}
            </div>
          ))}
          {workout.description && (
            <div className="mt-2 border-t border-whoop-border/50 pt-2 text-[11px] leading-relaxed text-whoop-text-secondary whitespace-pre-line">
              {workout.description}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

interface TrainingCalendarProps {
  from: string;
  to: string;
}

export function TrainingCalendar({ from, to }: TrainingCalendarProps) {
  const fromDate = new Date(from + "T00:00:00");
  const toDate = new Date(to + "T00:00:00");

  const [viewDate, setViewDate] = useState(() => toDate);

  const calFrom = new Date(viewDate.getFullYear(), viewDate.getMonth(), 1);
  const calTo = new Date(viewDate.getFullYear(), viewDate.getMonth() + 1, 0);
  const calFromStr = toLocalDateStr(calFrom);
  const calToStr = toLocalDateStr(calTo);

  const { data, loading } = useAerobicCalendar(calFromStr, calToStr);

  const year = viewDate.getFullYear();
  const month = viewDate.getMonth();
  const firstDay = new Date(year, month, 1);
  const startOffset = (firstDay.getDay() + 6) % 7;
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const todayStr = toLocalDateStr(new Date());

  const minMonth = new Date(fromDate.getFullYear(), fromDate.getMonth(), 1);
  const maxMonth = new Date(toDate.getFullYear(), toDate.getMonth(), 1);
  const canPrev = new Date(year, month - 1, 1) >= minMonth;
  const canNext = new Date(year, month + 1, 1) <= maxMonth;

  const prevMonth = () => { if (canPrev) setViewDate(new Date(year, month - 1, 1)); };
  const nextMonth = () => { if (canNext) setViewDate(new Date(year, month + 1, 1)); };

  const plannedByDate: Record<string, CalendarPlannedWorkout[]> = {};
  const completedByDate: Record<string, CalendarCompletedWorkout[]> = {};
  if (data) {
    for (const w of data.completed) {
      (completedByDate[w.date] ??= []).push(w);
    }
    // Only show planned workouts that don't have a matching completed workout
    for (const w of data.planned) {
      const completedTitles = (completedByDate[w.date] || []).map((c) => c.title?.toLowerCase());
      if (!completedTitles.includes(w.title?.toLowerCase())) {
        (plannedByDate[w.date] ??= []).push(w);
      }
    }
  }

  const monthLabel = firstDay.toLocaleDateString("en-US", { month: "long", year: "numeric" });

  // Build grid cells: empty padding + day cells
  const cells: { day: number; dateStr: string }[] = [];
  for (let i = 0; i < daysInMonth; i++) {
    const day = i + 1;
    const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    cells.push({ day, dateStr });
  }

  return (
    <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-whoop-text">Training Calendar</h2>
        <div className="flex items-center gap-2">
          <button
            onClick={prevMonth}
            disabled={!canPrev}
            className="rounded p-1 text-whoop-text-muted hover:bg-whoop-surface disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <ChevronLeft size={16} />
          </button>
          <span className="text-xs font-medium text-whoop-text-secondary" style={{ minWidth: "130px", textAlign: "center" }}>
            {monthLabel}
          </span>
          <button
            onClick={nextMonth}
            disabled={!canNext}
            className="rounded p-1 text-whoop-text-muted hover:bg-whoop-surface disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <ChevronRight size={16} />
          </button>
        </div>
      </div>

      {loading && <div className="py-12 text-center text-xs text-whoop-text-muted">Loading...</div>}

      {!loading && (
        <>
          {/* Day headers */}
          <div className="grid grid-cols-7 border-b border-whoop-border">
            {DAYS.map((d) => (
              <div key={d} className="py-1.5 text-center text-[10px] font-semibold uppercase tracking-wider text-whoop-text-muted">
                {d}
              </div>
            ))}
          </div>

          {/* Calendar grid */}
          <div className="grid grid-cols-7">
            {/* Empty cells for offset */}
            {Array.from({ length: startOffset }).map((_, i) => (
              <div key={`empty-${i}`} className="min-h-[80px] border-b border-r border-whoop-border/30" />
            ))}

            {cells.map(({ day, dateStr }) => {
              const planned = plannedByDate[dateStr] || [];
              const completed = completedByDate[dateStr] || [];
              const isToday = dateStr === todayStr;
              const isPast = dateStr < todayStr;
              const colIndex = (startOffset + day - 1) % 7;
              const isLastCol = colIndex === 6;

              return (
                <div
                  key={day}
                  className={`min-h-[80px] border-b border-whoop-border/30 p-1 ${
                    !isLastCol ? "border-r border-whoop-border/30" : ""
                  } ${isToday ? "bg-whoop-surface/50" : ""}`}
                >
                  {/* Day number */}
                  <div className={`mb-0.5 text-[11px] ${
                    isToday
                      ? "font-bold text-whoop-text"
                      : isPast
                        ? "text-whoop-text-muted"
                        : "text-whoop-text-secondary"
                  }`}>
                    {day}
                  </div>

                  {/* Workouts */}
                  <div className="space-y-0.5">
                    {completed.map((w, i) => (
                      <WorkoutBlock key={`c-${i}`} workout={w} />
                    ))}
                    {planned.map((w, i) => (
                      <WorkoutBlock key={`p-${i}`} workout={w} planned />
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
