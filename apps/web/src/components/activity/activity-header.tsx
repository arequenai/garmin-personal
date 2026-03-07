import Link from "next/link";
import { format } from "date-fns";
import {
  Activity as ActivityIcon,
  ArrowLeft,
  Bike,
  Dumbbell,
  Footprints,
  Waves,
} from "lucide-react";

import { formatDurationSec } from "@/lib/format";
import type { Activity } from "@/lib/types";

function ActivityTypeIcon({
  type,
  size,
}: {
  type: string | null;
  size: number;
}) {
  const key = type?.toLowerCase().replace(/\s+/g, "_") ?? "";
  switch (key) {
    case "running":
      return <Footprints size={size} />;
    case "cycling":
      return <Bike size={size} />;
    case "swimming":
      return <Waves size={size} />;
    case "strength_training":
      return <Dumbbell size={size} />;
    default:
      return <ActivityIcon size={size} />;
  }
}

interface ActivityHeaderProps {
  activity: Activity;
}

export function ActivityHeader({ activity }: ActivityHeaderProps) {
  const displayDate = format(
    new Date(activity.date + "T00:00:00"),
    "MMMM d, yyyy",
  );
  const duration =
    activity.duration_sec != null
      ? formatDurationSec(activity.duration_sec)
      : null;

  return (
    <div className="space-y-4">
      <Link
        href="/"
        className="inline-flex items-center gap-1.5 text-sm text-text-secondary transition-colors hover:text-text-primary"
      >
        <ArrowLeft size={16} />
        Back
      </Link>

      <div className="flex items-center gap-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-bg-hover text-text-primary">
          <ActivityTypeIcon type={activity.type} size={24} />
        </div>
        <div>
          <h1 className="font-heading text-3xl font-bold tracking-tight text-text-primary">
            {activity.name ?? "Unnamed Activity"}
          </h1>
          <p className="mt-0.5 text-sm text-text-secondary">
            {[activity.type ?? "Activity", displayDate, duration]
              .filter(Boolean)
              .join(" \u00B7 ")}
          </p>
        </div>
      </div>
    </div>
  );
}
