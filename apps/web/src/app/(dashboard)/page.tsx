import { format } from "date-fns";
import { RefreshCw } from "lucide-react";

import { BodyBatteryCard } from "@/components/dashboard/body-battery-card";
import { LatestActivity } from "@/components/dashboard/latest-activity";
import { MacroSplit } from "@/components/dashboard/macro-split";
import { RecoveryScore } from "@/components/dashboard/recovery-score";
import { TodaySummary } from "@/components/dashboard/today-summary";
import { fetchApi } from "@/lib/api";
import type { DashboardData } from "@/lib/types";

async function getDashboardData(): Promise<DashboardData | null> {
  try {
    return await fetchApi<DashboardData>("/api/dashboard/today");
  } catch {
    return null;
  }
}

export default async function DashboardPage() {
  const data = await getDashboardData();

  const displayDate = data?.date
    ? format(new Date(data.date + "T00:00:00"), "EEEE, MMM d, yyyy")
    : format(new Date(), "EEEE, MMM d, yyyy");

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      {/* ── Header ─────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-heading text-3xl font-bold tracking-tight text-text-primary">
            Today
          </h1>
          <p className="mt-1 text-sm text-text-secondary">{displayDate}</p>
        </div>

        <a
          href="/"
          className="flex h-10 w-10 items-center justify-center rounded-xl bg-bg-card text-text-secondary transition-colors hover:bg-bg-hover hover:text-text-primary"
          title="Refresh"
        >
          <RefreshCw size={18} />
        </a>
      </div>

      {/* ── Top row: Recovery + Body Battery ────────────── */}
      <div className="grid gap-4 md:grid-cols-2">
        <RecoveryScore
          performance={data?.performance ?? null}
          sleep={data?.sleep ?? null}
        />
        <BodyBatteryCard daily={data?.daily_summary ?? null} />
      </div>

      {/* ── Summary metrics ────────────────────────────── */}
      <TodaySummary
        daily={data?.daily_summary ?? null}
        sleep={data?.sleep ?? null}
      />

      {/* ── Latest Activity ────────────────────────────── */}
      <LatestActivity activity={data?.latest_activity ?? null} />

      {/* ── Macros ─────────────────────────────────────── */}
      <MacroSplit nutrition={data?.nutrition ?? null} />
    </div>
  );
}
