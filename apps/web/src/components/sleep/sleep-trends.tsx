"use client";

import type { SleepSession } from "@/lib/types";
import { TrendChart } from "@/components/ui/trend-chart";

interface SleepTrendsProps {
  data: SleepSession[];
}

type TrendDataPoint = Record<string, unknown> & {
  date: string;
  sleepScore: number | null;
  hrv: number | null;
};

function formatDateLabel(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function SleepTrends({ data }: SleepTrendsProps) {
  const sorted = [...data].sort(
    (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime(),
  );

  const trendData: TrendDataPoint[] = sorted.map((s) => ({
    date: formatDateLabel(s.date),
    sleepScore: s.sleep_score,
    hrv: s.avg_hrv,
  }));

  const hasScoreData = trendData.some((d) => d.sleepScore != null);
  const hasHrvData = trendData.some((d) => d.hrv != null);

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {/* Sleep Score Trend */}
      <div className="rounded-2xl bg-bg-card p-6">
        <h2 className="mb-4 font-heading text-lg font-semibold text-text-primary">
          Sleep Score Trend
        </h2>
        {hasScoreData ? (
          <TrendChart
            data={trendData}
            dataKey="sleepScore"
            color="#6366f1"
            height={200}
          />
        ) : (
          <div className="flex h-[200px] items-center justify-center text-text-secondary">
            No sleep score data available
          </div>
        )}
      </div>

      {/* HRV Trend */}
      <div className="rounded-2xl bg-bg-card p-6">
        <h2 className="mb-4 font-heading text-lg font-semibold text-text-primary">
          HRV Trend
        </h2>
        {hasHrvData ? (
          <TrendChart
            data={trendData}
            dataKey="hrv"
            color="#22c55e"
            height={200}
          />
        ) : (
          <div className="flex h-[200px] items-center justify-center text-text-secondary">
            No HRV data available
          </div>
        )}
      </div>
    </div>
  );
}
