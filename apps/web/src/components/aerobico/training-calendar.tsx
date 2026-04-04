"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import type { CalendarPlannedWorkout, CalendarCompletedWorkout } from "@/lib/types";
import { useAerobicCalendar } from "@/lib/hooks/use-aerobic-calendar";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

const WORKOUT_COLORS: Record<string, string> = {
  run: "#00d68f",
  bike: "#4da6ff",
  swim: "#00c4b4",
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
  if (!sec) return "--";
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  return h > 0 ? `${h}h${m}m` : `${m}m`;
}

function formatKm(meters: number | null): string {
  if (!meters) return "--";
  return `${(meters / 1000).toFixed(1)}km`;
}

interface DayPopoverProps {
  planned: CalendarPlannedWorkout[];
  completed: CalendarCompletedWorkout[];
}

function DayPopover({ planned, completed }: DayPopoverProps) {
  return (
    <div className="absolute left-1/2 top-full z-50 mt-1 -translate-x-1/2 rounded-lg border border-whoop-border bg-whoop-card p-2.5 shadow-lg"
         style={{ minWidth: "180px" }}>
      {completed.map((w, i) => (
        <div key={`c-${i}`} className="mb-1.5 last:mb-0">
          <div className="flex items-center gap-1.5">
            <div className="h-2 w-2 rounded-full" style={{ background: getColor(w.workout_type) }} />
            <span className="text-xs font-medium text-whoop-text">{w.title || "Workout"}</span>
          </div>
          <div className="ml-3.5 text-[10px] text-whoop-text-muted">
            TSS {w.tss ?? "--"} · {formatKm(w.distance_m)} · {formatDuration(w.duration_sec)}
          </div>
        </div>
      ))}
      {planned.map((w, i) => (
        <div key={`p-${i}`} className="mb-1.5 last:mb-0 opacity-60">
          <div className="flex items-center gap-1.5">
            <div className="h-2 w-2 rounded-full border border-dashed"
                 style={{ borderColor: getColor(w.workout_type) }} />
            <span className="text-xs font-medium text-whoop-text">{w.title || "Planned"}</span>
          </div>
          <div className="ml-3.5 text-[10px] text-whoop-text-muted">
            TSS {w.tss_planned ?? "--"} · {formatKm(w.distance_m_planned)} · {formatDuration(w.duration_sec_planned)}
          </div>
        </div>
      ))}
    </div>
  );
}

export function TrainingCalendar() {
  const [viewDate, setViewDate] = useState(() => new Date());
  const [selectedDay, setSelectedDay] = useState<string | null>(null);

  const from = new Date(viewDate.getFullYear(), viewDate.getMonth(), 1);
  const to = new Date(viewDate.getFullYear(), viewDate.getMonth() + 1, 0);
  const fromStr = from.toISOString().split("T")[0];
  const toStr = to.toISOString().split("T")[0];

  const { data, loading } = useAerobicCalendar(fromStr, toStr);

  const year = viewDate.getFullYear();
  const month = viewDate.getMonth();
  const firstDay = new Date(year, month, 1);
  const startOffset = (firstDay.getDay() + 6) % 7;
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const todayStr = new Date().toISOString().split("T")[0];

  const prevMonth = () => setViewDate(new Date(year, month - 1, 1));
  const nextMonth = () => setViewDate(new Date(year, month + 1, 1));

  const plannedByDate: Record<string, CalendarPlannedWorkout[]> = {};
  const completedByDate: Record<string, CalendarCompletedWorkout[]> = {};
  if (data) {
    for (const w of data.planned) {
      (plannedByDate[w.date] ??= []).push(w);
    }
    for (const w of data.completed) {
      (completedByDate[w.date] ??= []).push(w);
    }
  }

  const monthLabel = firstDay.toLocaleDateString("en-US", { month: "long", year: "numeric" });

  return (
    <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-whoop-text">Training Calendar</h2>
        <div className="flex items-center gap-2">
          <button onClick={prevMonth} className="rounded p-1 text-whoop-text-muted hover:bg-whoop-surface">
            <ChevronLeft size={16} />
          </button>
          <span className="text-xs font-medium text-whoop-text-secondary" style={{ minWidth: "120px", textAlign: "center" }}>
            {monthLabel}
          </span>
          <button onClick={nextMonth} className="rounded p-1 text-whoop-text-muted hover:bg-whoop-surface">
            <ChevronRight size={16} />
          </button>
        </div>
      </div>

      {loading && <div className="py-8 text-center text-xs text-whoop-text-muted">Loading...</div>}

      {!loading && (
        <>
          <div className="grid grid-cols-7 gap-px mb-1">
            {DAYS.map((d) => (
              <div key={d} className="text-center text-[9px] font-medium text-whoop-text-muted py-1">
                {d}
              </div>
            ))}
          </div>

          <div className="grid grid-cols-7 gap-px">
            {Array.from({ length: startOffset }).map((_, i) => (
              <div key={`empty-${i}`} className="h-10" />
            ))}
            {Array.from({ length: daysInMonth }).map((_, i) => {
              const day = i + 1;
              const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
              const planned = plannedByDate[dateStr] || [];
              const completed = completedByDate[dateStr] || [];
              const hasWorkout = planned.length > 0 || completed.length > 0;
              const isToday = dateStr === todayStr;
              const isSelected = dateStr === selectedDay;

              return (
                <div
                  key={day}
                  className={`relative flex h-10 cursor-pointer flex-col items-center justify-center rounded-md transition-colors ${
                    isToday ? "bg-whoop-surface" : "hover:bg-whoop-surface/50"
                  }`}
                  onClick={() => setSelectedDay(isSelected ? null : hasWorkout ? dateStr : null)}
                >
                  <span className={`text-[11px] ${isToday ? "font-bold text-whoop-text" : "text-whoop-text-secondary"}`}>
                    {day}
                  </span>
                  {hasWorkout && (
                    <div className="mt-0.5 flex gap-0.5">
                      {completed.length > 0 && (
                        <div className="h-1.5 w-1.5 rounded-full" style={{ background: getColor(completed[0].workout_type) }} />
                      )}
                      {planned.length > 0 && (
                        <div className="h-1.5 w-1.5 rounded-full border" style={{ borderColor: getColor(planned[0].workout_type) }} />
                      )}
                    </div>
                  )}
                  {isSelected && hasWorkout && (
                    <DayPopover planned={planned} completed={completed} />
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
