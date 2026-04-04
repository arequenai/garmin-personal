"use client";

import { useMemo } from "react";
import type { NutritionDay } from "@/lib/types";

interface AlcoholStripProps {
  data: NutritionDay[];
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

export function AlcoholStrip({ data }: AlcoholStripProps) {
  const sorted = useMemo(
    () => [...data].sort((a, b) => a.date.localeCompare(b.date)),
    [data],
  );

  if (sorted.length === 0) {
    return (
      <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
        <h2 className="mb-3 text-sm font-semibold text-whoop-text">Alcohol</h2>
        <div className="py-4 text-center text-xs text-whoop-text-muted">No data</div>
      </div>
    );
  }

  const dotSize = Math.max(6, Math.min(12, Math.floor(600 / sorted.length) - 2));
  const gap = 2;
  const svgHeight = 24;
  const cy = svgHeight / 2;

  // Detect week boundaries
  const weekBoundaries: number[] = [];
  for (let i = 1; i < sorted.length; i++) {
    if (getISOWeek(sorted[i].date) !== getISOWeek(sorted[i - 1].date)) {
      weekBoundaries.push(i);
    }
  }

  const svgWidth = sorted.length * (dotSize + gap);

  return (
    <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
      <h2 className="mb-3 text-sm font-semibold text-whoop-text">
        Alcohol
        <span className="ml-2 text-xs font-normal text-whoop-text-muted">
          <span style={{ color: "#f97316" }}>●</span> drink day{" · "}
          <span style={{ color: "#333" }}>●</span> none{" · "}
          <span style={{ color: "#444" }}>|</span> week
        </span>
      </h2>

      <div className="overflow-x-auto">
        <svg
          width={svgWidth}
          height={svgHeight}
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
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

          {sorted.map((d, i) => {
            const cx = i * (dotSize + gap) + dotSize / 2;
            const hasDrinks = (d.alcohol_drinks ?? 0) > 0;
            return (
              <circle
                key={d.date}
                cx={cx}
                cy={cy}
                r={dotSize / 2}
                fill={hasDrinks ? "#f97316" : "#333"}
              >
                <title>
                  {d.date}: {d.alcohol_drinks ?? 0} drink{(d.alcohol_drinks ?? 0) !== 1 ? "s" : ""}
                </title>
              </circle>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
