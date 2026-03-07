"use client";

import { useState } from "react";
import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

import type { PerformanceMetric } from "@/lib/types";

type TimeRange = "30d" | "90d" | "6m" | "1y" | "all";

interface PMCDataPoint {
  date: string;
  ctl: number | null;
  atl: number | null;
  tsb: number | null;
}

interface PMCChartProps {
  data: PerformanceMetric[];
}

const TIME_RANGES: { key: TimeRange; label: string }[] = [
  { key: "30d", label: "30d" },
  { key: "90d", label: "90d" },
  { key: "6m", label: "6m" },
  { key: "1y", label: "1y" },
  { key: "all", label: "All" },
];

function getDaysForRange(range: TimeRange): number {
  switch (range) {
    case "30d":
      return 30;
    case "90d":
      return 90;
    case "6m":
      return 180;
    case "1y":
      return 365;
    case "all":
      return Infinity;
  }
}

function formatDateLabel(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function PMCChart({ data }: PMCChartProps) {
  const [range, setRange] = useState<TimeRange>("90d");

  const sortedData = [...data].sort(
    (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime(),
  );

  const days = getDaysForRange(range);
  const filteredData =
    days === Infinity
      ? sortedData
      : sortedData.slice(-days);

  const chartData: PMCDataPoint[] = filteredData.map((d) => ({
    date: d.date,
    ctl: d.ctl,
    atl: d.atl,
    tsb: d.tsb,
  }));

  if (chartData.length === 0) {
    return (
      <div className="rounded-2xl bg-bg-card p-6">
        <h2 className="font-heading text-lg font-semibold text-text-primary">
          Performance Management Chart
        </h2>
        <div className="flex h-[350px] items-center justify-center text-text-secondary">
          No performance data available yet
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl bg-bg-card p-6">
      {/* Header with time range selector */}
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="font-heading text-lg font-semibold text-text-primary">
          Performance Management Chart
        </h2>
        <div className="flex gap-1 rounded-xl bg-bg-primary p-1">
          {TIME_RANGES.map((tr) => (
            <button
              key={tr.key}
              onClick={() => setRange(tr.key)}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                range === tr.key
                  ? "bg-bg-hover text-text-primary"
                  : "text-text-secondary hover:text-text-primary"
              }`}
            >
              {tr.label}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={350}>
        <ComposedChart
          data={chartData}
          margin={{ top: 8, right: 12, bottom: 0, left: -8 }}
        >
          <defs>
            <linearGradient id="tsbGradientPos" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#22c55e" stopOpacity={0.3} />
              <stop offset="100%" stopColor="#22c55e" stopOpacity={0.02} />
            </linearGradient>
          </defs>

          <XAxis
            dataKey="date"
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#6b6b7b", fontSize: 11 }}
            tickFormatter={formatDateLabel}
            interval="preserveStartEnd"
            minTickGap={50}
          />

          <YAxis
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#6b6b7b", fontSize: 11 }}
            width={40}
          />

          <Tooltip
            contentStyle={{
              backgroundColor: "#12121a",
              border: "none",
              borderRadius: "0.75rem",
              boxShadow: "0 4px 24px rgba(0,0,0,0.4)",
              color: "#e8e8ed",
              fontSize: "0.8125rem",
            }}
            labelFormatter={(label: unknown) => formatDateLabel(String(label))}
            labelStyle={{ color: "#6b6b7b", marginBottom: 4 }}
            formatter={(value: unknown, name: unknown) => {
              const labels: Record<string, string> = {
                ctl: "CTL (Fitness)",
                atl: "ATL (Fatigue)",
                tsb: "TSB (Form)",
              };
              const num = typeof value === "number" ? value.toFixed(1) : "-";
              const key = String(name ?? "");
              return [num, labels[key] || key];
            }}
            cursor={{ stroke: "#6b6b7b", strokeWidth: 1, strokeDasharray: "4 4" }}
          />

          <Legend
            verticalAlign="top"
            align="right"
            iconType="circle"
            iconSize={8}
            formatter={(value: string) => {
              const labels: Record<string, string> = {
                ctl: "CTL (Fitness)",
                atl: "ATL (Fatigue)",
                tsb: "TSB (Form)",
              };
              return (
                <span className="text-xs text-text-secondary">
                  {labels[value] || value}
                </span>
              );
            }}
            wrapperStyle={{ paddingBottom: 8 }}
          />

          {/* TSB area */}
          <Area
            type="monotone"
            dataKey="tsb"
            stroke="none"
            fill="url(#tsbGradientPos)"
            fillOpacity={1}
            dot={false}
            activeDot={false}
            connectNulls
          />

          {/* CTL line (Fitness) */}
          <Line
            type="monotone"
            dataKey="ctl"
            stroke="#6366f1"
            strokeWidth={2}
            dot={false}
            activeDot={{
              r: 4,
              fill: "#6366f1",
              stroke: "#12121a",
              strokeWidth: 2,
            }}
            connectNulls
          />

          {/* ATL line (Fatigue) */}
          <Line
            type="monotone"
            dataKey="atl"
            stroke="#f97316"
            strokeWidth={2}
            dot={false}
            activeDot={{
              r: 4,
              fill: "#f97316",
              stroke: "#12121a",
              strokeWidth: 2,
            }}
            connectNulls
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
