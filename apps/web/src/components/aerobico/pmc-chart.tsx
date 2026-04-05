"use client";

import { useEffect, useRef } from "react";
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

export function PMCChart({ data, from, to }: PMCChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

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
      data.filter((d) => d.ctl != null).map((d) => ({ time: d.date, value: d.ctl! })),
    );

    const atlSeries = chart.addSeries(LineSeriesDef, {
      color: "#f97316",
      lineWidth: 2,
      title: "ATL",
    });
    atlSeries.setData(
      data.filter((d) => d.atl != null).map((d) => ({ time: d.date, value: d.atl! })),
    );

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
      data.filter((d) => d.tsb != null).map((d) => ({ time: d.date, value: d.tsb! })),
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
        Performance Management Chart
      </h2>
      <div ref={containerRef} />
    </div>
  );
}
