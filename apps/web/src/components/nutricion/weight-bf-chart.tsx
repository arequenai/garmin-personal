"use client";

import { useEffect, useRef } from "react";
import {
  createChart,
  type IChartApi,
  LineSeries as LineSeriesDef,
} from "lightweight-charts";
import type { BodyCompositionDay } from "@/lib/types";
import { BASE_CHART_OPTIONS } from "@/lib/chart-config";

interface WeightBFChartProps {
  data: BodyCompositionDay[];
  from: string;
  to: string;
}

export function WeightBFChart({ data, from, to }: WeightBFChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      ...BASE_CHART_OPTIONS,
      width: containerRef.current.clientWidth,
      height: 200,
      rightPriceScale: { borderColor: "#2a2a2a", visible: true },
      leftPriceScale: { borderColor: "#2a2a2a", visible: true },
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
      <div ref={containerRef} />
    </div>
  );
}
