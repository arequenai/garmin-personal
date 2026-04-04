"use client";

import { useEffect, useRef } from "react";
import {
  createChart,
  type IChartApi,
  ColorType,
  LineSeries as LineSeriesDef,
} from "lightweight-charts";
import type { BodyCompositionDay } from "@/lib/types";

interface WeightBFChartProps {
  data: BodyCompositionDay[];
  from: string;
  to: string;
}

export function WeightBFChart({ data, from, to }: WeightBFChartProps) {
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
      rightPriceScale: { borderColor: "#2a2a2a", visible: true },
      leftPriceScale: { borderColor: "#2a2a2a", visible: true },
      timeScale: { borderColor: "#2a2a2a" },
    });
    chartRef.current = chart;

    const sorted = [...data].sort((a, b) => a.date.localeCompare(b.date));

    const weightSeries = chart.addSeries(LineSeriesDef, {
      color: "#4da6ff",
      lineWidth: 2,
      priceScaleId: "left",
      title: "Weight (kg)",
    });
    weightSeries.setData(
      sorted.filter((d) => d.weight_kg != null).map((d) => ({ time: d.date, value: d.weight_kg! })),
    );

    const bfSeries = chart.addSeries(LineSeriesDef, {
      color: "#f97316",
      lineWidth: 2,
      priceScaleId: "right",
      title: "Body Fat (%)",
    });
    bfSeries.setData(
      sorted
        .filter((d) => d.body_fat_pct != null)
        .map((d) => ({ time: d.date, value: d.body_fat_pct! })),
    );

    // Anchor the time axis to the full date range even if data is sparse
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
  }, [data, from, to]);

  return (
    <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
      <h2 className="mb-3 text-sm font-semibold text-whoop-text">
        Weight & Body Fat
        <span className="ml-2 text-xs font-normal text-whoop-text-muted">
          weight (blue) · body fat (orange)
        </span>
      </h2>
      {data.length === 0 ? (
        <div className="py-8 text-center text-xs text-whoop-text-muted">No body composition data</div>
      ) : (
        <div ref={containerRef} />
      )}
    </div>
  );
}
