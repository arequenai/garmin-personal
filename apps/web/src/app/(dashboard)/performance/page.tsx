import { format, subDays } from "date-fns";
import { Activity as ActivityIcon, Heart, TrendingUp, Zap } from "lucide-react";

import { ActivityCalendar } from "@/components/performance/activity-calendar";
import { LoadDistribution } from "@/components/performance/load-distribution";
import { PMCChart } from "@/components/performance/pmc-chart";
import { MetricCard } from "@/components/ui/metric-card";
import { fetchApi } from "@/lib/api";
import type { Activity, PerformanceMetric } from "@/lib/types";

async function getPerformanceData(): Promise<PerformanceMetric[]> {
  try {
    const toDate = format(new Date(), "yyyy-MM-dd");
    const fromDate = format(subDays(new Date(), 365), "yyyy-MM-dd");
    return await fetchApi<PerformanceMetric[]>(
      `/api/performance?from_date=${fromDate}&to_date=${toDate}`,
    );
  } catch {
    return [];
  }
}

async function getActivities(): Promise<Activity[]> {
  try {
    const toDate = format(new Date(), "yyyy-MM-dd");
    const fromDate = format(subDays(new Date(), 365), "yyyy-MM-dd");
    return await fetchApi<Activity[]>(
      `/api/activities?from_date=${fromDate}&to_date=${toDate}`,
    );
  } catch {
    return [];
  }
}

function getLatestVo2max(activities: Activity[]): number | null {
  for (const a of activities) {
    if (a.vo2max_estimate != null) return a.vo2max_estimate;
  }
  return null;
}

export default async function PerformancePage() {
  const [performanceData, activities] = await Promise.all([
    getPerformanceData(),
    getActivities(),
  ]);

  // The API returns data ordered by date desc; the latest entry is first
  const latest = performanceData.length > 0 ? performanceData[0] : null;
  const vo2max = getLatestVo2max(activities);

  const tsbValue = latest?.tsb ?? 0;
  const tsbColor =
    tsbValue >= 0 ? "text-recovery" : "text-alert";

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      {/* Header */}
      <div>
        <h1 className="font-heading text-3xl font-bold tracking-tight text-text-primary">
          Performance
        </h1>
        <p className="mt-1 text-sm text-text-secondary">
          Training Load &amp; Fitness Trends
        </p>
      </div>

      {/* PMC Chart (full width) */}
      <PMCChart data={performanceData} />

      {/* Activity Calendar + Load Distribution */}
      <div className="grid gap-4 md:grid-cols-2">
        <ActivityCalendar activities={activities} />
        <LoadDistribution activities={activities} />
      </div>

      {/* Current Metrics */}
      <div>
        <h2 className="mb-3 text-sm font-medium text-text-secondary">
          Current Metrics
        </h2>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <MetricCard
            label="CTL (Fitness)"
            value={latest?.ctl?.toFixed(1) ?? "--"}
            icon={<TrendingUp size={18} />}
            accentColor="text-sleep"
          />
          <MetricCard
            label="ATL (Fatigue)"
            value={latest?.atl?.toFixed(1) ?? "--"}
            icon={<Zap size={18} />}
            accentColor="text-strain"
          />
          <MetricCard
            label="TSB (Form)"
            value={latest?.tsb?.toFixed(1) ?? "--"}
            icon={<ActivityIcon size={18} />}
            accentColor={tsbColor}
          />
          <MetricCard
            label="VO2max"
            value={vo2max?.toFixed(0) ?? "--"}
            unit="ml/kg/min"
            icon={<Heart size={18} />}
            accentColor="text-recovery"
          />
        </div>
      </div>
    </div>
  );
}
