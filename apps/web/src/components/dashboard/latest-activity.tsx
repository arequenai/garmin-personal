import Link from "next/link";
import {
  Bike,
  Dumbbell,
  Footprints,
  HeartPulse,
  Timer,
  Waves,
  Zap,
} from "lucide-react";

import { formatDistanceKm, formatDurationSec } from "@/lib/format";
import type { Activity } from "@/lib/types";

interface LatestActivityProps {
  activity: Activity | null;
}

const typeConfig: Record<
  string,
  { icon: typeof Footprints; color: string; borderColor: string }
> = {
  running: {
    icon: Footprints,
    color: "text-recovery",
    borderColor: "border-l-recovery",
  },
  cycling: {
    icon: Bike,
    color: "text-strain",
    borderColor: "border-l-strain",
  },
  swimming: {
    icon: Waves,
    color: "text-sleep",
    borderColor: "border-l-sleep",
  },
  strength_training: {
    icon: Dumbbell,
    color: "text-alert",
    borderColor: "border-l-alert",
  },
  cardio: {
    icon: Zap,
    color: "text-strain",
    borderColor: "border-l-strain",
  },
};

function getTypeConfig(type: string | null) {
  if (!type) return typeConfig.running;
  const key = type.toLowerCase().replace(/\s+/g, "_");
  return typeConfig[key] ?? typeConfig.running;
}

export function LatestActivity({ activity }: LatestActivityProps) {
  if (!activity) {
    return (
      <div className="rounded-2xl bg-bg-card p-6">
        <span className="text-sm font-medium tracking-wide text-text-secondary uppercase">
          Latest Activity
        </span>
        <p className="mt-4 text-text-secondary">No activities recorded today</p>
      </div>
    );
  }

  const config = getTypeConfig(activity.type);
  const Icon = config.icon;

  const stats: Array<{ label: string; value: string; icon: typeof Timer }> = [];

  if (activity.distance_m != null) {
    stats.push({
      label: "Distance",
      value: `${formatDistanceKm(activity.distance_m)} km`,
      icon: Footprints,
    });
  }
  if (activity.duration_sec != null) {
    stats.push({
      label: "Duration",
      value: formatDurationSec(activity.duration_sec),
      icon: Timer,
    });
  }
  if (activity.avg_hr != null) {
    stats.push({
      label: "Avg HR",
      value: `${activity.avg_hr} bpm`,
      icon: HeartPulse,
    });
  }
  if (activity.tss != null) {
    stats.push({
      label: "TSS",
      value: String(Math.round(activity.tss)),
      icon: Zap,
    });
  }

  return (
    <Link
      href={`/activities/${activity.id}`}
      className="group block"
    >
      <div
        className={`rounded-2xl border-l-4 bg-bg-card p-6 transition-colors duration-200 group-hover:bg-bg-hover ${config.borderColor}`}
      >
        <span className="text-sm font-medium tracking-wide text-text-secondary uppercase">
          Latest Activity
        </span>

        <div className="mt-4 flex items-center gap-3">
          <div
            className={`flex h-10 w-10 items-center justify-center rounded-xl bg-bg-hover ${config.color}`}
          >
            <Icon size={20} />
          </div>
          <div>
            <h3 className="font-heading text-lg font-semibold text-text-primary">
              {activity.name ?? "Unnamed Activity"}
            </h3>
            <p className="text-xs text-text-secondary">
              {activity.type ?? "Activity"}
            </p>
          </div>
        </div>

        {stats.length > 0 && (
          <div className="mt-5 flex flex-wrap gap-6">
            {stats.map((stat) => (
              <div key={stat.label} className="flex items-center gap-2">
                <stat.icon size={14} className="text-text-secondary" />
                <div>
                  <p className="text-xs text-text-secondary">{stat.label}</p>
                  <p className="font-heading text-sm font-semibold text-text-primary">
                    {stat.value}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Link>
  );
}
