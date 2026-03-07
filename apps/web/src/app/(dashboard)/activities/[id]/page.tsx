import { ArrowLeft } from "lucide-react";
import Link from "next/link";

import { ActivityHeader } from "@/components/activity/activity-header";
import { ActivityMetrics } from "@/components/activity/activity-metrics";
import { fetchApi } from "@/lib/api";
import type { Activity } from "@/lib/types";

async function getActivity(id: string): Promise<Activity | null> {
  try {
    return await fetchApi<Activity>(`/api/activities/${id}`);
  } catch {
    return null;
  }
}

export default async function ActivityPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const activity = await getActivity(id);

  if (!activity) {
    return (
      <div className="mx-auto max-w-5xl space-y-6">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-sm text-text-secondary transition-colors hover:text-text-primary"
        >
          <ArrowLeft size={16} />
          Back
        </Link>
        <div className="rounded-2xl bg-bg-card p-12 text-center">
          <h2 className="font-heading text-2xl font-bold text-text-primary">
            Activity not found
          </h2>
          <p className="mt-2 text-sm text-text-secondary">
            The activity you are looking for does not exist or could not be
            loaded.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <ActivityHeader activity={activity} />
      <ActivityMetrics activity={activity} />
    </div>
  );
}
