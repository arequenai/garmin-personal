"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Cell,
} from "recharts";

import type { NutritionDaily } from "@/lib/types";

interface CalorieTrendProps {
  data: NutritionDaily[];
  target?: number;
}

interface ChartDataPoint {
  date: string;
  label: string;
  calories: number;
  overTarget: boolean;
}

function formatDateLabel(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

const NORMAL_COLOR = "#6366f1";
const OVER_COLOR = "#ef4444";

export function CalorieTrend({ data, target = 2500 }: CalorieTrendProps) {
  const sortedData = [...data].sort(
    (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime(),
  );

  const chartData: ChartDataPoint[] = sortedData.map((d) => {
    const cal = d.calories ?? 0;
    return {
      date: d.date,
      label: formatDateLabel(d.date),
      calories: cal,
      overTarget: cal > target * 1.15,
    };
  });

  if (chartData.length === 0) {
    return (
      <div className="rounded-2xl bg-bg-card p-6">
        <h2 className="font-heading text-lg font-semibold text-text-primary">
          Calorie Trend
        </h2>
        <div className="flex h-[300px] items-center justify-center text-text-secondary">
          No calorie data available yet
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl bg-bg-card p-6">
      <h2 className="mb-4 font-heading text-lg font-semibold text-text-primary">
        Calorie Trend
      </h2>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart
          data={chartData}
          margin={{ top: 8, right: 12, bottom: 0, left: -8 }}
        >
          <XAxis
            dataKey="label"
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#6b6b7b", fontSize: 11 }}
            interval="preserveStartEnd"
            minTickGap={40}
          />
          <YAxis
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#6b6b7b", fontSize: 11 }}
            width={45}
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
            formatter={(value: unknown) => {
              const num =
                typeof value === "number" ? value.toLocaleString("en-US") : "-";
              return [num, "Calories"];
            }}
            cursor={{ fill: "rgba(255,255,255,0.04)" }}
          />
          <ReferenceLine
            y={target}
            stroke="#6b6b7b"
            strokeDasharray="6 4"
            label={{
              value: `Target: ${target.toLocaleString("en-US")}`,
              fill: "#6b6b7b",
              fontSize: 11,
              position: "insideTopRight",
            }}
          />
          <Bar dataKey="calories" radius={[4, 4, 0, 0]} maxBarSize={32}>
            {chartData.map((entry) => (
              <Cell
                key={entry.date}
                fill={entry.overTarget ? OVER_COLOR : NORMAL_COLOR}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
