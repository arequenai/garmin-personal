"use client";

import { useMemo } from "react";
import type { NutritionDay } from "@/lib/types";

interface AlcoholStripProps {
  data: NutritionDay[];
  from: string;
  to: string;
}

function getISOWeek(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  d.setDate(d.getDate() + 3 - ((d.getDay() + 6) % 7));
  const yearStart = new Date(d.getFullYear(), 0, 4);
  const weekNo = Math.ceil(
    ((d.getTime() - yearStart.getTime()) / 86400000 + yearStart.getDay() + 1) / 7,
  );
  return `${d.getFullYear()}-W${String(weekNo).padStart(2, "0")}`;
}

function generateDateRange(from: string, to: string): string[] {
  const dates: string[] = [];
  const d = new Date(from + "T00:00:00");
  const end = new Date(to + "T00:00:00");
  while (d <= end) {
    dates.push(d.toISOString().split("T")[0]);
    d.setDate(d.getDate() + 1);
  }
  return dates;
}

interface DayAlcohol {
  date: string;
  drinks: number | null; // null = no data for this day
}

export function AlcoholStrip({ data, from, to }: AlcoholStripProps) {
  const days = useMemo(() => {
    const dataMap = new Map<string, NutritionDay>();
    for (const d of data) {
      dataMap.set(d.date, d);
    }

    return generateDateRange(from, to).map((date): DayAlcohol => {
      const d = dataMap.get(date);
      return { date, drinks: d ? (d.alcohol_drinks ?? 0) : null };
    });
  }, [data, from, to]);

  if (days.length === 0) {
    return (
      <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
        <h2 className="mb-3 text-sm font-semibold text-whoop-text">Alcohol</h2>
        <div className="py-4 text-center text-xs text-whoop-text-muted">No data</div>
      </div>
    );
  }

  const gap = 2;
  const dotSize = Math.max(6, Math.min(12, Math.floor(600 / days.length) - gap));
  const svgHeight = 24;
  const cy = svgHeight / 2;
  const svgWidth = days.length * (dotSize + gap);

  // Detect week boundaries
  const weekBoundaries: number[] = [];
  for (let i = 1; i < days.length; i++) {
    if (getISOWeek(days[i].date) !== getISOWeek(days[i - 1].date)) {
      weekBoundaries.push(i);
    }
  }

  return (
    <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
      <h2 className="mb-3 text-sm font-semibold text-whoop-text">
        Alcohol
        <span className="ml-2 text-xs font-normal text-whoop-text-muted">
          <span style={{ color: "#f97316" }}>●</span> drink day{" · "}
          <span style={{ color: "#555" }}>●</span> none{" · "}
          <span style={{ color: "#333" }}>●</span> no data{" · "}
          <span style={{ color: "#444" }}>|</span> week
        </span>
      </h2>

      <div className="overflow-x-auto">
        <svg
          width="100%"
          height={svgHeight}
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          preserveAspectRatio="none"
          className="block"
        >
          {weekBoundaries.map((idx) => {
            const x = idx * (dotSize + gap) - gap / 2;
            return (
              <line
                key={`wb-${idx}`}
                x1={x}
                y1={0}
                x2={x}
                y2={svgHeight}
                stroke="#444"
                strokeWidth={1}
              />
            );
          })}

          {days.map((d, i) => {
            const cx = i * (dotSize + gap) + dotSize / 2;
            const fill =
              d.drinks === null ? "#333" : d.drinks > 0 ? "#f97316" : "#555";
            return (
              <circle
                key={d.date}
                cx={cx}
                cy={cy}
                r={dotSize / 2}
                fill={fill}
              >
                <title>
                  {d.date}: {d.drinks === null ? "no data" : `${d.drinks} drink${d.drinks !== 1 ? "s" : ""}`}
                </title>
              </circle>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
