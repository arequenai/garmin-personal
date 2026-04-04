"use client";

import { useEffect, useRef } from "react";
import {
  createChart,
  type IChartApi,
  ColorType,
} from "lightweight-charts";
import type { PMCDataPoint } from "@/lib/types";

interface PMCChartProps {
  data: PMCDataPoint[];
}

export function PMCChart({ data }: PMCChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: 350,
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

    const ctlSeries = chart.addLineSeries({
      color: "#4da6ff",
      lineWidth: 2,
      title: "CTL",
    });
    ctlSeries.setData(
      data.filter((d) => d.ctl != null).map((d) => ({ time: d.date, value: d.ctl! })),
    );

    const atlSeries = chart.addLineSeries({
      color: "#f97316",
      lineWidth: 2,
      title: "ATL",
    });
    atlSeries.setData(
      data.filter((d) => d.atl != null).map((d) => ({ time: d.date, value: d.atl! })),
    );

    const tsbSeries = chart.addBaselineSeries({
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
      data.filter((d) => d.tsb != null).map((d) => ({ time: d.date, value: d.tsb! })),
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
        Performance Management Chart
      </h2>
      <div ref={containerRef} />
    </div>
  );
}
