import { format, subDays } from "date-fns";
import { Activity, Battery, Droplets, Heart } from "lucide-react";

import { BodyBatteryPattern } from "@/components/body/body-battery-pattern";
import { RestingHrTrend } from "@/components/body/resting-hr-trend";
import { StressHeatmap } from "@/components/body/stress-heatmap";
import { MetricCard } from "@/components/ui/metric-card";
import { fetchApi } from "@/lib/api";
import type { DailySummary } from "@/lib/types";

async function getDailySummaries(): Promise<DailySummary[]> {
  try {
    const toDate = format(new Date(), "yyyy-MM-dd");
    const fromDate = format(subDays(new Date(), 30), "yyyy-MM-dd");
    return await fetchApi<DailySummary[]>(
      `/api/daily?from_date=${fromDate}&to_date=${toDate}`,
    );
  } catch {
    return [];
  }
}

export default async function BodyPage() {
  const dailyData = await getDailySummaries();

  // Latest day's data (API returns desc order, first entry is most recent)
  const today = dailyData.length > 0 ? dailyData[0] : null;

  const hydrationLiters =
    today?.hydration_ml != null ? (today.hydration_ml / 1000).toFixed(1) : "--";

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      {/* Header */}
      <div>
        <h1 className="font-heading text-3xl font-bold tracking-tight text-text-primary">
          Body &amp; Health
        </h1>
        <p className="mt-1 text-sm text-text-secondary">
          Vital Signs &amp; Recovery Patterns
        </p>
      </div>

      {/* Charts row: Resting HR + Body Battery */}
      <div className="grid gap-4 md:grid-cols-2">
        <RestingHrTrend data={dailyData} />
        <BodyBatteryPattern data={dailyData} />
      </div>

      {/* Stress Heatmap (full width) */}
      <StressHeatmap data={dailyData} />

      {/* Current Metrics */}
      <div>
        <h2 className="mb-3 text-sm font-medium text-text-secondary">
          Current Metrics
        </h2>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <MetricCard
            label="Resting HR"
            value={today?.resting_hr ?? "--"}
            unit="bpm"
            icon={<Heart size={18} />}
            accentColor="text-alert"
          />
          <MetricCard
            label="Avg Stress"
            value={today?.stress_avg ?? "--"}
            icon={<Activity size={18} />}
            accentColor="text-strain"
          />
          <MetricCard
            label="Body Battery"
            value={today?.body_battery_high ?? "--"}
            unit="/100"
            icon={<Battery size={18} />}
            accentColor="text-recovery"
          />
          <MetricCard
            label="Hydration"
            value={hydrationLiters}
            unit="L"
            icon={<Droplets size={18} />}
            accentColor="text-sleep"
          />
        </div>
      </div>
    </div>
  );
}
