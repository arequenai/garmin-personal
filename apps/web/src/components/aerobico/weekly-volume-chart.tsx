"use client";

import { useEffect, useRef } from "react";
import {
  createChart,
  type IChartApi,
  ColorType,
} from "lightweight-charts";
import type { WeeklyVolume } from "@/lib/types";

interface WeeklyVolumeChartProps {
  data: WeeklyVolume[];
}

export function WeeklyVolumeChart({ data }: WeeklyVolumeChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!containerRef.current || data.length === 0) return;

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: 250,
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

    const kmSeries = chart.addHistogramSeries({
      color: "#4da6ff",
      priceScaleId: "left",
      title: "km",
    });
    kmSeries.setData(
      data.map((d) => ({ time: d.week_start, value: d.km })),
    );

    const elevSeries = chart.addLineSeries({
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
