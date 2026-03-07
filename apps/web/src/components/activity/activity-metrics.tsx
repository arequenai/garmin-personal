import {
  Flame,
  Heart,
  HeartPulse,
  Mountain,
  Ruler,
  Zap,
} from "lucide-react";

import { MetricCard } from "@/components/ui/metric-card";
import { formatDistanceKm, formatNumber } from "@/lib/format";
import type { Activity } from "@/lib/types";

interface ActivityMetricsProps {
  activity: Activity;
}

function getBarColor(value: number): string {
  if (value >= 4) return "bg-red-500";
  if (value >= 3) return "bg-orange-500";
  if (value >= 2) return "bg-blue-500";
  return "bg-green-500";
}

function TrainingEffectBar({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  const pct = Math.min((value / 5) * 100, 100);

  return (
    <div className="flex-1">
      <div className="mb-1.5 flex items-baseline gap-2">
        <span className="text-sm text-text-secondary">{label}</span>
        <span className="font-heading text-sm font-semibold text-text-primary">
          {value.toFixed(1)}
        </span>
      </div>
      <div className="h-2.5 w-full rounded-full bg-bg-hover">
        <div
          className={`h-2.5 rounded-full transition-all ${getBarColor(value)}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export function ActivityMetrics({ activity }: ActivityMetricsProps) {
  const hasTrainingEffects =
    activity.training_effect_aerobic != null ||
    activity.training_effect_anaerobic != null;
  const hasPower = activity.avg_power != null;
  const hasVo2max = activity.vo2max_estimate != null;

  return (
    <div className="space-y-4">
      {/* ── Main metrics grid ──────────────────────────── */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        <MetricCard
          label="Distance"
          value={
            activity.distance_m != null
              ? formatDistanceKm(activity.distance_m)
              : "—"
          }
          unit="km"
          icon={<Ruler size={16} />}
        />
        <MetricCard
          label="Avg HR"
          value={activity.avg_hr != null ? activity.avg_hr : "—"}
          unit="bpm"
          icon={<HeartPulse size={16} />}
        />
        <MetricCard
          label="Max HR"
          value={activity.max_hr != null ? activity.max_hr : "—"}
          unit="bpm"
          icon={<Heart size={16} />}
        />
        <MetricCard
          label="TSS"
          value={
            activity.tss != null ? activity.tss.toFixed(1) : "—"
          }
          icon={<Zap size={16} />}
        />
        <MetricCard
          label="Calories"
          value={
            activity.calories != null
              ? formatNumber(activity.calories)
              : "—"
          }
          icon={<Flame size={16} />}
        />
        <MetricCard
          label="Elevation"
          value={
            activity.elevation_gain != null
              ? Math.round(activity.elevation_gain)
              : "—"
          }
          unit="m"
          icon={<Mountain size={16} />}
        />
      </div>

      {/* ── Training Effects ───────────────────────────── */}
      {hasTrainingEffects && (
        <div className="rounded-2xl bg-bg-card p-6">
          <h3 className="mb-4 text-sm font-medium tracking-wide text-text-secondary uppercase">
            Training Effects
          </h3>
          <div className="flex flex-col gap-4 sm:flex-row sm:gap-8">
            {activity.training_effect_aerobic != null && (
              <TrainingEffectBar
                label="Aerobic"
                value={activity.training_effect_aerobic}
              />
            )}
            {activity.training_effect_anaerobic != null && (
              <TrainingEffectBar
                label="Anaerobic"
                value={activity.training_effect_anaerobic}
              />
            )}
          </div>
        </div>
      )}

      {/* ── Power ──────────────────────────────────────── */}
      {hasPower && (
        <div className="rounded-2xl bg-bg-card p-6">
          <h3 className="mb-3 text-sm font-medium tracking-wide text-text-secondary uppercase">
            Power
          </h3>
          <p className="font-heading text-lg font-semibold text-text-primary">
            Avg: {activity.avg_power}W
            {activity.max_power != null && (
              <span className="text-text-secondary">
                {" "}
                &middot; Max: {activity.max_power}W
              </span>
            )}
          </p>
        </div>
      )}

      {/* ── VO2max ─────────────────────────────────────── */}
      {hasVo2max && (
        <div className="rounded-2xl bg-bg-card p-6">
          <h3 className="mb-3 text-sm font-medium tracking-wide text-text-secondary uppercase">
            VO2max Estimate
          </h3>
          <p className="font-heading text-3xl font-bold tracking-tight text-recovery">
            {activity.vo2max_estimate}
          </p>
        </div>
      )}
    </div>
  );
}
