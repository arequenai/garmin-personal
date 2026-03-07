"use client";

import { useMemo, useState } from "react";
import { format, subWeeks, startOfWeek, addDays, addWeeks } from "date-fns";

import type { Activity } from "@/lib/types";

interface ActivityCalendarProps {
  activities: Activity[];
}

const WEEKS_TO_SHOW = 20;

const INTENSITY_COLORS = [
  "bg-bg-hover",         // 0 TSS
  "bg-emerald-900/60",   // 1-30
  "bg-emerald-700/70",   // 30-60
  "bg-emerald-500/80",   // 60-100
  "bg-emerald-400",      // 100+
] as const;

function getIntensityLevel(tss: number): number {
  if (tss === 0) return 0;
  if (tss <= 30) return 1;
  if (tss <= 60) return 2;
  if (tss <= 100) return 3;
  return 4;
}

const DAY_LABELS = ["Mon", "", "Wed", "", "Fri", "", "Sun"];

export function ActivityCalendar({ activities }: ActivityCalendarProps) {
  const [hoveredCell, setHoveredCell] = useState<{
    date: string;
    tss: number;
    x: number;
    y: number;
  } | null>(null);

  const { tssByDate, weeks, monthLabels } = useMemo(() => {
    // Build a map of date -> total TSS
    const tssMap = new Map<string, number>();
    for (const a of activities) {
      const dateKey = a.date;
      const current = tssMap.get(dateKey) ?? 0;
      tssMap.set(dateKey, current + (a.tss ?? 0));
    }

    // Generate the weeks grid
    const today = new Date();
    const startDate = startOfWeek(subWeeks(today, WEEKS_TO_SHOW - 1), {
      weekStartsOn: 1,
    });

    const generatedWeeks: string[][] = [];
    const months: { label: string; col: number }[] = [];
    let lastMonth = -1;

    for (let w = 0; w < WEEKS_TO_SHOW; w++) {
      const weekStart = addWeeks(startDate, w);
      const week: string[] = [];

      for (let d = 0; d < 7; d++) {
        const day = addDays(weekStart, d);
        const dateStr = format(day, "yyyy-MM-dd");

        // Track month labels
        if (d === 0) {
          const month = day.getMonth();
          if (month !== lastMonth) {
            months.push({
              label: format(day, "MMM"),
              col: w,
            });
            lastMonth = month;
          }
        }

        // Only include dates up to today
        if (day <= today) {
          week.push(dateStr);
        } else {
          week.push("");
        }
      }
      generatedWeeks.push(week);
    }

    return { tssByDate: tssMap, weeks: generatedWeeks, monthLabels: months };
  }, [activities]);

  return (
    <div className="rounded-2xl bg-bg-card p-6">
      <h2 className="mb-4 font-heading text-lg font-semibold text-text-primary">
        Activity Calendar
      </h2>

      <div className="relative overflow-x-auto">
        {/* Month labels row */}
        <div className="mb-1 flex" style={{ paddingLeft: "28px" }}>
          {weeks.map((_, wIdx) => {
            const monthLabel = monthLabels.find((m) => m.col === wIdx);
            return (
              <div
                key={wIdx}
                className="text-[10px] text-text-secondary"
                style={{ width: "16px", minWidth: "16px" }}
              >
                {monthLabel?.label ?? ""}
              </div>
            );
          })}
        </div>

        {/* Grid */}
        <div className="flex gap-0">
          {/* Day labels */}
          <div className="mr-1 flex flex-col gap-[2px]">
            {DAY_LABELS.map((label, i) => (
              <div
                key={i}
                className="flex h-3 items-center text-[10px] text-text-secondary"
                style={{ width: "24px" }}
              >
                {label}
              </div>
            ))}
          </div>

          {/* Week columns */}
          {weeks.map((week, wIdx) => (
            <div key={wIdx} className="flex flex-col gap-[2px]">
              {week.map((dateStr, dIdx) => {
                if (!dateStr) {
                  return (
                    <div
                      key={dIdx}
                      className="h-3 w-3 rounded-sm"
                      style={{ minWidth: "12px" }}
                    />
                  );
                }

                const tss = tssByDate.get(dateStr) ?? 0;
                const level = getIntensityLevel(tss);

                return (
                  <div
                    key={dIdx}
                    className={`h-3 w-3 rounded-sm transition-colors ${INTENSITY_COLORS[level]}`}
                    style={{ minWidth: "12px" }}
                    onMouseEnter={(e) => {
                      const rect = e.currentTarget.getBoundingClientRect();
                      setHoveredCell({
                        date: dateStr,
                        tss,
                        x: rect.left + rect.width / 2,
                        y: rect.top,
                      });
                    }}
                    onMouseLeave={() => setHoveredCell(null)}
                  />
                );
              })}
            </div>
          ))}
        </div>

        {/* Legend */}
        <div className="mt-3 flex items-center gap-1 text-[10px] text-text-secondary">
          <span>Less</span>
          {INTENSITY_COLORS.map((color, i) => (
            <div key={i} className={`h-3 w-3 rounded-sm ${color}`} />
          ))}
          <span>More</span>
        </div>
      </div>

      {/* Tooltip */}
      {hoveredCell && (
        <div
          className="pointer-events-none fixed z-50 rounded-lg bg-bg-primary px-3 py-1.5 text-xs text-text-primary shadow-lg"
          style={{
            left: hoveredCell.x,
            top: hoveredCell.y - 36,
            transform: "translateX(-50%)",
          }}
        >
          <span className="text-text-secondary">
            {format(new Date(hoveredCell.date + "T00:00:00"), "MMM d, yyyy")}
          </span>
          {" "}
          <span className="font-medium">{Math.round(hoveredCell.tss)} TSS</span>
        </div>
      )}
    </div>
  );
}
