import { format, subDays } from "date-fns";
import { Clock, Droplets, Heart, Moon } from "lucide-react";

import { SleepArchitecture } from "@/components/sleep/sleep-architecture";
import { SleepTrends } from "@/components/sleep/sleep-trends";
import { MetricCard } from "@/components/ui/metric-card";
import { fetchApi } from "@/lib/api";
import { formatDurationMin } from "@/lib/format";
import type { SleepSession } from "@/lib/types";

export const dynamic = "force-dynamic";

async function getSleepData(): Promise<SleepSession[]> {
  try {
    const toDate = format(new Date(), "yyyy-MM-dd");
    const fromDate = format(subDays(new Date(), 30), "yyyy-MM-dd");
    return await fetchApi<SleepSession[]>(
      `/api/sleep?from_date=${fromDate}&to_date=${toDate}`,
    );
  } catch {
    return [];
  }
}

export default async function SleepPage() {
  const sleepData = await getSleepData();

  // The API returns data ordered by date desc; the latest entry is first
  const latest = sleepData.length > 0 ? sleepData[0] : null;

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      {/* Header */}
      <div>
        <h1 className="font-heading text-3xl font-bold tracking-tight text-text-primary">
          Sleep
        </h1>
        <p className="mt-1 text-sm text-text-secondary">
          Sleep Analysis &amp; Trends
        </p>
      </div>

      {/* Sleep Architecture (stacked horizontal bars, last 14 nights) */}
      <SleepArchitecture data={sleepData} />

      {/* Sleep Score + HRV Trends (side by side, 30 days) */}
      <SleepTrends data={sleepData} />

      {/* Current Metrics */}
      <div>
        <h2 className="mb-3 text-sm font-medium text-text-secondary">
          Last Night
        </h2>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <MetricCard
            label="Sleep Score"
            value={latest?.sleep_score ?? "--"}
            icon={<Moon size={18} />}
            accentColor="text-sleep"
          />
          <MetricCard
            label="Total Sleep"
            value={
              latest?.total_sleep_min != null
                ? formatDurationMin(latest.total_sleep_min)
                : "--"
            }
            icon={<Clock size={18} />}
            accentColor="text-sleep"
          />
          <MetricCard
            label="Avg HR"
            value={latest?.avg_hr_sleep ?? "--"}
            unit="bpm"
            icon={<Heart size={18} />}
            accentColor="text-strain"
          />
          <MetricCard
            label="SpO2"
            value={
              latest?.avg_spo2_sleep != null
                ? `${latest.avg_spo2_sleep.toFixed(1)}%`
                : "--"
            }
            icon={<Droplets size={18} />}
            accentColor="text-recovery"
          />
        </div>
      </div>
    </div>
  );
}
