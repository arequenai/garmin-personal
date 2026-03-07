import { Activity, Flame, Footprints, Moon } from "lucide-react";

import { MetricCard } from "@/components/ui/metric-card";
import { formatDurationMin, formatNumber } from "@/lib/format";
import type { DailySummary, SleepSession } from "@/lib/types";

interface TodaySummaryProps {
  daily: DailySummary | null;
  sleep: SleepSession | null;
}

export function TodaySummary({ daily, sleep }: TodaySummaryProps) {
  const sleepValue =
    sleep?.total_sleep_min != null
      ? formatDurationMin(sleep.total_sleep_min)
      : "\u2014";

  const stressValue =
    daily?.stress_avg != null ? String(daily.stress_avg) : "\u2014";

  const stepsValue =
    daily?.steps != null ? formatNumber(daily.steps) : "\u2014";

  const caloriesValue =
    daily?.calories_total != null
      ? formatNumber(daily.calories_total)
      : "\u2014";

  const activeCalories =
    daily?.calories_active != null
      ? `Active: ${formatNumber(daily.calories_active)}`
      : undefined;

  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      <MetricCard
        label="Sleep"
        value={sleepValue}
        icon={<Moon size={18} />}
        accentColor="text-sleep"
      />
      <MetricCard
        label="Stress"
        value={stressValue}
        icon={<Activity size={18} />}
        accentColor="text-strain"
      />
      <MetricCard
        label="Steps"
        value={stepsValue}
        icon={<Footprints size={18} />}
        accentColor="text-text-primary"
      />
      <MetricCard
        label="Calories"
        value={caloriesValue}
        unit={activeCalories}
        icon={<Flame size={18} />}
        accentColor="text-alert"
      />
    </div>
  );
}
