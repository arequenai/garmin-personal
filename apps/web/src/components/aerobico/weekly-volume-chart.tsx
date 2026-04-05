"use client";

import { useEffect, useRef } from "react";
import {
  createChart,
  type IChartApi,
  HistogramSeries as HistogramSeriesDef,
  LineSeries as LineSeriesDef,
} from "lightweight-charts";
import type { WeeklyVolume } from "@/lib/types";
import { BASE_CHART_OPTIONS } from "@/lib/chart-config";

interface WeeklyVolumeChartProps {
  data: WeeklyVolume[];
  from: string;
  to: string;
}

export function WeeklyVolumeChart({ data, from, to }: WeeklyVolumeChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      ...BASE_CHART_OPTIONS,
      width: containerRef.current.clientWidth,
      height: 250,
      rightPriceScale: { borderColor: "#2a2a2a", visible: true },
      leftPriceScale: { borderColor: "#2a2a2a", visible: true },
    });
    chartRef.current = chart;

    const kmSeries = chart.addSeries(HistogramSeriesDef, {
      color: "#4da6ff",
      priceScaleId: "left",
      title: "km",
    });
    kmSeries.setData(
      data.map((d) => ({ time: d.week_start, value: d.km })),
    );

    const elevSeries = chart.addSeries(LineSeriesDef, {
      color: "#f97316",
      lineWidth: 2,
      priceScaleId: "right",
      title: "elevation (m)",
    });
    elevSeries.setData(
      data.map((d) => ({ time: d.week_start, value: d.elevation_m })),
    );

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
  }, [data, from, to]);

  return (
    <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
      <h2 className="mb-3 text-sm font-semibold text-whoop-text">
        Weekly Volume
        <span className="ml-2 text-xs font-normal text-whoop-text-muted">
          km (blue) · elevation (orange)
        </span>
      </h2>
      <div ref={containerRef} />
    </div>
  );
}
