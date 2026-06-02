"use client";

import { useEffect, useRef, useState } from "react";
import {
  createChart,
  type IChartApi,
  LineSeries as LineSeriesDef,
  BaselineSeries as BaselineSeriesDef,
} from "lightweight-charts";
import type { PMCDataPoint } from "@/lib/types";
import { BASE_CHART_OPTIONS } from "@/lib/chart-config";

interface PMCChartProps {
  data: PMCDataPoint[];
  from: string;
  to: string;
}

type PMCView = "daily" | "weekly";

// Parse a YYYY-MM-DD string as UTC to get a timezone-stable weekday.
function isMonday(date: string): boolean {
  const [year, month, day] = date.split("-").map(Number);
  return new Date(Date.UTC(year, month - 1, day)).getUTCDay() === 1;
}

export function PMCChart({ data, from, to }: PMCChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const [view, setView] = useState<PMCView>("daily");

  useEffect(() => {
    if (!containerRef.current) return;

    // In weekly view, keep only Mondays and show CTL/ATL (no TSB or daily TSS).
    const weekly = view === "weekly";
    const points = weekly ? data.filter((d) => isMonday(d.date)) : data;

    const chart = createChart(containerRef.current, {
      ...BASE_CHART_OPTIONS,
      width: containerRef.current.clientWidth,
      height: 350,
    });
    chartRef.current = chart;

    const ctlSeries = chart.addSeries(LineSeriesDef, {
      color: "#4da6ff",
      lineWidth: 2,
      title: "CTL",
    });
    ctlSeries.setData(
      points.filter((d) => d.ctl != null).map((d) => ({ time: d.date, value: d.ctl! })),
    );

    const atlSeries = chart.addSeries(LineSeriesDef, {
      color: "#f97316",
      lineWidth: 2,
      title: "ATL",
    });
    atlSeries.setData(
      points.filter((d) => d.atl != null).map((d) => ({ time: d.date, value: d.atl! })),
    );

    if (!weekly) {
      const tsbSeries = chart.addSeries(BaselineSeriesDef, {
        baseValue: { type: "price", price: 0 },
        topLineColor: "#00d68f",
        topFillColor1: "rgba(0, 214, 143, 0.2)",
        topFillColor2: "rgba(0, 214, 143, 0.0)",
        bottomLineColor: "#ef4444",
        bottomFillColor1: "rgba(239, 68, 68, 0.0)",
        bottomFillColor2: "rgba(239, 68, 68, 0.2)",
        lineWidth: 2,
        title: "TSB",
      });
      tsbSeries.setData(
        points.filter((d) => d.tsb != null).map((d) => ({ time: d.date, value: d.tsb! })),
      );
    }

    // Anchor the time axis to the selected date range
    const anchorSeries = chart.addSeries(LineSeriesDef, {
      color: "transparent",
      lineWidth: 1,
      crosshairMarkerVisible: false,
      lastValueVisible: false,
      priceLineVisible: false,
      priceScaleId: "",
    });
    anchorSeries.setData([
      { time: from, value: 0 },
      { time: to, value: 0 },
    ]);
    chart.timeScale().setVisibleRange({ from, to });

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
  }, [data, from, to, view]);

  return (
    <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-whoop-text">
          Performance Management Chart
        </h2>
        <div className="flex overflow-hidden rounded-md border border-whoop-border text-xs">
          {(["daily", "weekly"] as const).map((v) => (
            <button
              key={v}
              type="button"
              onClick={() => setView(v)}
              className={`px-3 py-1 font-medium transition-colors ${
                view === v
                  ? "bg-whoop-surface text-whoop-text"
                  : "text-whoop-text-secondary hover:text-whoop-text"
              }`}
            >
              {v === "daily" ? "Diario" : "Semanal"}
            </button>
          ))}
        </div>
      </div>
      <div ref={containerRef} />
    </div>
  );
}
