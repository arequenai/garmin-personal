"use client";

import {
  Area,
  AreaChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  ReferenceLine,
} from "recharts";

import type { DailySummary } from "@/lib/types";

interface RestingHrTrendProps {
  data: DailySummary[];
}

function formatDateLabel(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function RestingHrTrend({ data }: RestingHrTrendProps) {
  const chartData = [...data]
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
    .filter((d) => d.resting_hr != null)
    .map((d) => ({
      date: d.date,
      resting_hr: d.resting_hr,
    }));

  if (chartData.length === 0) {
    return (
      <div className="rounded-2xl bg-bg-card p-6">
        <h2 className="font-heading text-lg font-semibold text-text-primary">
          Resting Heart Rate
        </h2>
        <div className="flex h-[250px] items-center justify-center text-text-secondary">
          No resting HR data available
        </div>
      </div>
    );
  }

  const hrValues = chartData
    .map((d) => d.resting_hr)
    .filter((v): v is number => v != null);
  const avgHr = Math.round(
    hrValues.reduce((sum, v) => sum + v, 0) / hrValues.length,
  );

  return (
    <div className="rounded-2xl bg-bg-card p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-heading text-lg font-semibold text-text-primary">
          Resting Heart Rate
        </h2>
        <span className="text-xs text-text-secondary">Avg: {avgHr} bpm</span>
      </div>

      <ResponsiveContainer width="100%" height={250}>
        <AreaChart
          data={chartData}
          margin={{ top: 4, right: 4, bottom: 0, left: -8 }}
        >
          <defs>
            <linearGradient id="hrGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#ef4444" stopOpacity={0.25} />
              <stop offset="100%" stopColor="#ef4444" stopOpacity={0} />
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
            width={36}
            domain={["dataMin - 3", "dataMax + 3"]}
          />

          <ReferenceLine
            y={avgHr}
            stroke="#6b6b7b"
            strokeDasharray="4 4"
            strokeWidth={1}
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
            formatter={(value: unknown) => [`${value} bpm`, "Resting HR"]}
            cursor={{
              stroke: "#ef4444",
              strokeWidth: 1,
              strokeDasharray: "4 4",
            }}
          />

          <Area
            type="monotone"
            dataKey="resting_hr"
            stroke="#ef4444"
            strokeWidth={2}
            fill="url(#hrGradient)"
            dot={false}
            activeDot={{
              r: 4,
              fill: "#ef4444",
              stroke: "#12121a",
              strokeWidth: 2,
            }}
            connectNulls
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
