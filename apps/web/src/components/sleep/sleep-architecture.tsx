"use client";

import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { SleepSession } from "@/lib/types";
import { formatDurationMin } from "@/lib/format";

interface SleepArchitectureProps {
  data: SleepSession[];
}

interface ArchitectureDataPoint {
  date: string;
  dateLabel: string;
  deep: number;
  light: number;
  rem: number;
  awake: number;
  total: string;
}

const STAGE_COLORS = {
  deep: "#312e81",
  light: "#818cf8",
  rem: "#7c3aed",
  awake: "#ef4444",
} as const;

const STAGE_LABELS: Record<string, string> = {
  deep: "Deep",
  light: "Light",
  rem: "REM",
  awake: "Awake",
};

function formatDateLabel(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function SleepArchitecture({ data }: SleepArchitectureProps) {
  const sorted = [...data]
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
    .slice(0, 14);

  const chartData: ArchitectureDataPoint[] = sorted.reverse().map((s) => ({
    date: s.date,
    dateLabel: formatDateLabel(s.date),
    deep: s.deep_min ?? 0,
    light: s.light_min ?? 0,
    rem: s.rem_min ?? 0,
    awake: s.awake_min ?? 0,
    total: formatDurationMin(s.total_sleep_min ?? 0),
  }));

  if (chartData.length === 0) {
    return (
      <div className="rounded-2xl bg-bg-card p-6">
        <h2 className="font-heading text-lg font-semibold text-text-primary">
          Sleep Architecture
        </h2>
        <div className="flex h-[350px] items-center justify-center text-text-secondary">
          No sleep data available yet
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl bg-bg-card p-6">
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="font-heading text-lg font-semibold text-text-primary">
          Sleep Architecture
        </h2>
        <div className="flex flex-wrap gap-3">
          {Object.entries(STAGE_COLORS).map(([stage, color]) => (
            <div key={stage} className="flex items-center gap-1.5">
              <div
                className="h-2.5 w-2.5 rounded-sm"
                style={{ backgroundColor: color }}
              />
              <span className="text-xs text-text-secondary">
                {STAGE_LABELS[stage]}
              </span>
            </div>
          ))}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={chartData.length * 32 + 20}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 4, right: 60, bottom: 0, left: 4 }}
          barSize={18}
        >
          <XAxis
            type="number"
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#6b6b7b", fontSize: 11 }}
            tickFormatter={(v: number) => `${Math.round(v / 60)}h`}
          />

          <YAxis
            type="category"
            dataKey="dateLabel"
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#6b6b7b", fontSize: 11 }}
            width={52}
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
            labelStyle={{ color: "#6b6b7b", marginBottom: 4 }}
            formatter={(value: unknown, name: unknown) => {
              const mins = typeof value === "number" ? value : 0;
              const key = String(name ?? "");
              return [formatDurationMin(mins), STAGE_LABELS[key] || key];
            }}
            cursor={{ fill: "rgba(255,255,255,0.03)" }}
          />

          <Bar
            dataKey="deep"
            stackId="sleep"
            fill={STAGE_COLORS.deep}
            radius={[4, 0, 0, 4]}
          />
          <Bar
            dataKey="light"
            stackId="sleep"
            fill={STAGE_COLORS.light}
            radius={0}
          />
          <Bar
            dataKey="rem"
            stackId="sleep"
            fill={STAGE_COLORS.rem}
            radius={0}
          />
          <Bar
            dataKey="awake"
            stackId="sleep"
            fill={STAGE_COLORS.awake}
            radius={[0, 4, 4, 0]}
          />
        </BarChart>
      </ResponsiveContainer>

      {/* Total sleep labels on the right side */}
      <div className="mt-2 text-xs text-text-secondary">
        Last {chartData.length} nights
      </div>
    </div>
  );
}
