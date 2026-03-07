"use client";

import { useState } from "react";
import { format } from "date-fns";

import type { DailySummary } from "@/lib/types";

interface StressHeatmapProps {
  data: DailySummary[];
}

function stressColor(avg: number): string {
  if (avg < 25) return "bg-emerald-600";
  if (avg < 50) return "bg-yellow-500";
  if (avg < 75) return "bg-orange-500";
  return "bg-red-500";
}

function stressLabel(avg: number): string {
  if (avg < 25) return "Low";
  if (avg < 50) return "Medium";
  if (avg < 75) return "High";
  return "Very High";
}

export function StressHeatmap({ data }: StressHeatmapProps) {
  const [hoveredDay, setHoveredDay] = useState<{
    date: string;
    avg: number;
    max: number;
    x: number;
    y: number;
  } | null>(null);

  const chartData = [...data]
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
    .slice(-14)
    .filter((d) => d.stress_avg != null);

  if (chartData.length === 0) {
    return (
      <div className="rounded-2xl bg-bg-card p-6">
        <h2 className="font-heading text-lg font-semibold text-text-primary">
          Stress Levels
        </h2>
        <div className="flex h-[120px] items-center justify-center text-text-secondary">
          No stress data available
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl bg-bg-card p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-heading text-lg font-semibold text-text-primary">
          Stress Levels
        </h2>
        <span className="text-xs text-text-secondary">Last 14 days</span>
      </div>

      {/* Heatmap grid */}
      <div className="flex flex-wrap gap-2">
        {chartData.map((d) => {
          const avg = d.stress_avg ?? 0;
          return (
            <div key={d.date} className="flex flex-col items-center gap-1">
              <div
                className={`h-10 w-10 rounded-lg ${stressColor(avg)} cursor-default transition-transform hover:scale-110`}
                onMouseEnter={(e) => {
                  const rect = e.currentTarget.getBoundingClientRect();
                  setHoveredDay({
                    date: d.date,
                    avg,
                    max: d.stress_max ?? 0,
                    x: rect.left + rect.width / 2,
                    y: rect.top,
                  });
                }}
                onMouseLeave={() => setHoveredDay(null)}
              />
              <span className="text-[10px] text-text-secondary">
                {format(new Date(d.date + "T00:00:00"), "d")}
              </span>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="mt-4 flex items-center gap-3 text-[10px] text-text-secondary">
        <div className="flex items-center gap-1">
          <div className="h-3 w-3 rounded-sm bg-emerald-600" />
          <span>Low (&lt;25)</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="h-3 w-3 rounded-sm bg-yellow-500" />
          <span>Medium (25-49)</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="h-3 w-3 rounded-sm bg-orange-500" />
          <span>High (50-74)</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="h-3 w-3 rounded-sm bg-red-500" />
          <span>Very High (75+)</span>
        </div>
      </div>

      {/* Tooltip */}
      {hoveredDay && (
        <div
          className="pointer-events-none fixed z-50 rounded-lg bg-bg-primary px-3 py-2 text-xs text-text-primary shadow-lg"
          style={{
            left: hoveredDay.x,
            top: hoveredDay.y - 52,
            transform: "translateX(-50%)",
          }}
        >
          <div className="text-text-secondary">
            {format(new Date(hoveredDay.date + "T00:00:00"), "MMM d")}
            {" - "}
            {stressLabel(hoveredDay.avg)}
          </div>
          <div className="mt-0.5">
            Avg: <span className="font-medium">{hoveredDay.avg}</span>
            {" / "}
            Max: <span className="font-medium">{hoveredDay.max}</span>
          </div>
        </div>
      )}
    </div>
  );
}
