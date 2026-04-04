"use client";

import { useMemo, useRef, useState } from "react";
import type { NutritionDay } from "@/lib/types";

interface MacroStackedChartProps {
  data: NutritionDay[];
  from: string;
  to: string;
}

interface DayMacro {
  date: string;
  hasData: boolean;
  protein_pct: number;
  carbs_pct: number;
  fat_pct: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
}

const COLORS = {
  protein: "#4da6ff",
  carbs: "#00d68f",
  fat: "#f97316",
};

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

export function MacroStackedChart({ data, from, to }: MacroStackedChartProps) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const days = useMemo(() => {
    const dataMap = new Map<string, NutritionDay>();
    for (const d of data) {
      dataMap.set(d.date, d);
    }

    return generateDateRange(from, to).map((date): DayMacro => {
      const d = dataMap.get(date);
      if (!d || d.protein_g == null || d.carbs_g == null || d.fat_g == null) {
        return { date, hasData: false, protein_pct: 0, carbs_pct: 0, fat_pct: 0, protein_g: 0, carbs_g: 0, fat_g: 0 };
      }
      const p = d.protein_g;
      const c = d.carbs_g;
      const f = d.fat_g;
      const total = p + c + f;
      if (total === 0) {
        return { date, hasData: true, protein_pct: 0, carbs_pct: 0, fat_pct: 0, protein_g: 0, carbs_g: 0, fat_g: 0 };
      }
      return {
        date,
        hasData: true,
        protein_pct: (p / total) * 100,
        carbs_pct: (c / total) * 100,
        fat_pct: (f / total) * 100,
        protein_g: p,
        carbs_g: c,
        fat_g: f,
      };
    });
  }, [data, from, to]);

  if (days.length === 0) {
    return (
      <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
        <h2 className="mb-3 text-sm font-semibold text-whoop-text">Macro Split</h2>
        <div className="py-8 text-center text-xs text-whoop-text-muted">No macro data</div>
      </div>
    );
  }

  const gap = 1;
  const barWidth = Math.max(2, Math.min(12, Math.floor(600 / days.length) - gap));
  const svgWidth = days.length * (barWidth + gap);
  const svgHeight = 120;
  const hovered = hoveredIndex != null ? days[hoveredIndex] : null;

  return (
    <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
      <h2 className="mb-3 text-sm font-semibold text-whoop-text">
        Macro Split
        <span className="ml-2 text-xs font-normal text-whoop-text-muted">
          <span style={{ color: COLORS.protein }}>■</span> P{" "}
          <span style={{ color: COLORS.carbs }}>■</span> C{" "}
          <span style={{ color: COLORS.fat }}>■</span> F
        </span>
      </h2>

      {hovered && hovered.hasData && (
        <div className="mb-2 text-xs text-whoop-text-muted">
          {hovered.date}:{" "}
          <span style={{ color: COLORS.protein }}>P {Math.round(hovered.protein_g)}g ({hovered.protein_pct.toFixed(0)}%)</span>{" · "}
          <span style={{ color: COLORS.carbs }}>C {Math.round(hovered.carbs_g)}g ({hovered.carbs_pct.toFixed(0)}%)</span>{" · "}
          <span style={{ color: COLORS.fat }}>F {Math.round(hovered.fat_g)}g ({hovered.fat_pct.toFixed(0)}%)</span>
        </div>
      )}

      <div ref={containerRef} className="overflow-x-auto">
        <svg
          width="100%"
          height={svgHeight}
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          preserveAspectRatio="none"
          className="block"
        >
          {days.map((d, i) => {
            const x = i * (barWidth + gap);
            if (!d.hasData) {
              return (
                <rect
                  key={d.date}
                  x={x}
                  y={0}
                  width={barWidth}
                  height={svgHeight}
                  fill="#222"
                  onMouseEnter={() => setHoveredIndex(i)}
                  onMouseLeave={() => setHoveredIndex(null)}
                >
                  <title>{d.date}: no data</title>
                </rect>
              );
            }
            const proteinH = (d.protein_pct / 100) * svgHeight;
            const carbsH = (d.carbs_pct / 100) * svgHeight;
            const fatH = (d.fat_pct / 100) * svgHeight;
            return (
              <g
                key={d.date}
                onMouseEnter={() => setHoveredIndex(i)}
                onMouseLeave={() => setHoveredIndex(null)}
                style={{ cursor: "crosshair" }}
              >
                <rect x={x} y={0} width={barWidth} height={proteinH} fill={COLORS.protein} />
                <rect x={x} y={proteinH} width={barWidth} height={carbsH} fill={COLORS.carbs} />
                <rect x={x} y={proteinH + carbsH} width={barWidth} height={fatH} fill={COLORS.fat} />
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
