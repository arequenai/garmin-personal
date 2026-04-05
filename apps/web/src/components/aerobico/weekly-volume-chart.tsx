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
}

export function WeeklyVolumeChart({ data }: WeeklyVolumeChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!containerRef.current || data.length === 0) return;

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
        Weekly Volume
        <span className="ml-2 text-xs font-normal text-whoop-text-muted">
          km (blue) · elevation (orange)
        </span>
      </h2>
      {data.length === 0 ? (
        <div className="py-8 text-center text-xs text-whoop-text-muted">No volume data</div>
      ) : (
        <div ref={containerRef} />
      )}
    </div>
  );
}
