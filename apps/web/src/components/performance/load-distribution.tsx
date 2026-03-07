"use client";

import { useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { format, startOfWeek, subWeeks, addWeeks, isSameWeek } from "date-fns";

import type { Activity } from "@/lib/types";

interface LoadDistributionProps {
  activities: Activity[];
}

const CARDIO_TYPES = new Set([
  "running",
  "cycling",
  "swimming",
  "walking",
  "hiking",
  "trail_running",
  "open_water_swimming",
  "indoor_cycling",
  "treadmill_running",
  "elliptical",
  "rowing",
  "cardio",
]);

interface WeeklyLoad {
  week: string;
  cardio: number;
  strength: number;
}

export function LoadDistribution({ activities }: LoadDistributionProps) {
  const chartData: WeeklyLoad[] = useMemo(() => {
    const today = new Date();
    const weeksCount = 12;
    const weeksStart = startOfWeek(subWeeks(today, weeksCount - 1), {
      weekStartsOn: 1,
    });

    // Initialize weeks
    const weeks: WeeklyLoad[] = [];
    for (let i = 0; i < weeksCount; i++) {
      const wStart = addWeeks(weeksStart, i);
      weeks.push({
        week: format(wStart, "MMM d"),
        cardio: 0,
        strength: 0,
      });
    }

    // Distribute activities into weeks
    for (const a of activities) {
      const aDate = new Date(a.date + "T00:00:00");
      const tss = a.tss ?? 0;
      if (tss === 0) continue;

      const weekIdx = weeks.findIndex((_, i) => {
        const wStart = addWeeks(weeksStart, i);
        return isSameWeek(aDate, wStart, { weekStartsOn: 1 });
      });

      if (weekIdx === -1) continue;

      const actType = (a.type ?? "").toLowerCase().replace(/\s+/g, "_");
      if (CARDIO_TYPES.has(actType)) {
        weeks[weekIdx].cardio += tss;
      } else {
        weeks[weekIdx].strength += tss;
      }
    }

    return weeks.map((w) => ({
      ...w,
      cardio: Math.round(w.cardio),
      strength: Math.round(w.strength),
    }));
  }, [activities]);

  const hasData = chartData.some((w) => w.cardio > 0 || w.strength > 0);

  return (
    <div className="rounded-2xl bg-bg-card p-6">
      <h2 className="mb-4 font-heading text-lg font-semibold text-text-primary">
        Weekly Load Distribution
      </h2>

      {!hasData ? (
        <div className="flex h-[250px] items-center justify-center text-sm text-text-secondary">
          No activity data for the last 12 weeks
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={250}>
          <BarChart
            data={chartData}
            margin={{ top: 4, right: 4, bottom: 0, left: -16 }}
          >
            <XAxis
              dataKey="week"
              axisLine={false}
              tickLine={false}
              tick={{ fill: "#6b6b7b", fontSize: 10 }}
              interval={0}
              angle={-45}
              textAnchor="end"
              height={50}
            />

            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: "#6b6b7b", fontSize: 11 }}
              width={36}
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
                const labels: Record<string, string> = {
                  cardio: "Cardio",
                  strength: "Strength / Other",
                };
                const key = String(name ?? "");
                return [`${value} TSS`, labels[key] || key];
              }}
              cursor={{ fill: "rgba(255,255,255,0.04)" }}
            />

            <Legend
              verticalAlign="top"
              align="right"
              iconType="circle"
              iconSize={8}
              formatter={(value: string) => {
                const labels: Record<string, string> = {
                  cardio: "Cardio",
                  strength: "Strength / Other",
                };
                return (
                  <span className="text-xs text-text-secondary">
                    {labels[value] || value}
                  </span>
                );
              }}
              wrapperStyle={{ paddingBottom: 8 }}
            />

            <Bar
              dataKey="cardio"
              stackId="load"
              fill="#6366f1"
              radius={[0, 0, 0, 0]}
            />
            <Bar
              dataKey="strength"
              stackId="load"
              fill="#f97316"
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
