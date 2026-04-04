"use client";

import { useEffect, useRef } from "react";
import {
  createChart,
  type IChartApi,
  ColorType,
  HistogramSeries as HistogramSeriesDef,
  LineSeries as LineSeriesDef,
} from "lightweight-charts";
import type { NutritionDay } from "@/lib/types";

interface CaloriesChartProps {
  data: NutritionDay[];
}

function compute7dMA(data: NutritionDay[]): { time: string; value: number }[] {
  const sorted = [...data].sort((a, b) => a.date.localeCompare(b.date));
  const result: { time: string; value: number }[] = [];
  for (let i = 0; i < sorted.length; i++) {
    const windowStart = Math.max(0, i - 6);
    let sum = 0;
    let count = 0;
    for (let j = windowStart; j <= i; j++) {
      if (sorted[j].calories != null) {
        sum += sorted[j].calories!;
        count++;
      }
    }
    if (count > 0) {
      result.push({ time: sorted[i].date, value: Math.round(sum / count) });
    }
  }
  return result;
}

export function CaloriesChart({ data }: CaloriesChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!containerRef.current || data.length === 0) return;

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: 200,
      layout: {
        background: { type: ColorType.Solid, color: "#1a1a1a" },
        textColor: "#888888",
      },
      grid: {
        vertLines: { color: "#2a2a2a" },
        horzLines: { color: "#2a2a2a" },
      },
      crosshair: { mode: 0 },
      rightPriceScale: { borderColor: "#2a2a2a" },
      timeScale: { borderColor: "#2a2a2a" },
    });
    chartRef.current = chart;

    const sorted = [...data].sort((a, b) => a.date.localeCompare(b.date));

    // Use the most recent non-null goal value
    const goals = sorted.map((d) => d.calories_goal).filter((g): g is number => g != null);
    const goalValue = goals.length > 0 ? goals[goals.length - 1] : null;

    // Daily calorie bars — green if ≤ goal, red if > goal
    const barSeries = chart.addSeries(HistogramSeriesDef, {
      title: "Calories",
    });
    barSeries.setData(
      sorted
        .filter((d) => d.calories != null)
        .map((d) => ({
          time: d.date,
          value: d.calories!,
          color:
            goalValue != null && d.calories! > goalValue
              ? "#ef4444"
              : "#00d68f",
        })),
    );

    // Goal line
    if (goalValue != null) {
      const goalSeries = chart.addSeries(LineSeriesDef, {
        color: "#f97316",
        lineWidth: 1,
        lineStyle: 2,
        title: "Goal",
        crosshairMarkerVisible: false,
      });
      goalSeries.setData(
        sorted
          .filter((d) => d.calories != null)
          .map((d) => ({ time: d.date, value: goalValue })),
      );
    }

    // 7-day moving average
    const maSeries = chart.addSeries(LineSeriesDef, {
      color: "#4da6ff",
      lineWidth: 1,
      title: "7d avg",
      crosshairMarkerVisible: false,
    });
    maSeries.setData(compute7dMA(sorted));

    chart.timeScale().fitContent();

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, [data]);

  return (
    <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
      <h2 className="mb-3 text-sm font-semibold text-whoop-text">
        Calories vs Goal
        <span className="ml-2 text-xs font-normal text-whoop-text-muted">
          bars · goal (orange) · 7d avg (blue)
        </span>
      </h2>
      {data.length === 0 ? (
        <div className="py-8 text-center text-xs text-whoop-text-muted">No calorie data</div>
      ) : (
        <div ref={containerRef} />
      )}
    </div>
  );
}
