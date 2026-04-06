import { fetchApi } from "@/lib/api";
import { emptyPlanDailyData, type PlanDailyData } from "@/lib/types";
import { DailyStrip } from "@/components/plan/daily-strip";
import { PillarAccordion } from "@/components/plan/pillar-accordion";
import { SyncStatusBar } from "@/components/plan/sync-status-bar";

export const dynamic = "force-dynamic";

export default async function PlanPage() {
  let data: PlanDailyData;
  let loadError = false;
  try {
    data = await fetchApi<PlanDailyData>("/api/plan/daily");
  } catch {
    data = emptyPlanDailyData();
    loadError = true;
  }

  const isEmpty = data.strip.length === 0 && data.pillars.length === 0;

  return (
    <div className="min-h-screen bg-whoop-bg text-whoop-text">
      {/* Content */}
      <div className="mx-auto max-w-[1200px] px-3 pt-4 pb-20 sm:px-6 sm:pt-6 sm:pb-16">
        {isEmpty ? (
          <div className="flex flex-col items-center justify-center rounded-xl border border-whoop-border bg-whoop-card px-6 py-16 text-center">
            <p className="text-sm text-whoop-text-muted">
              {loadError
                ? "Could not load data. Make sure the API is running."
                : "No data available for today."}
            </p>
          </div>
        ) : (
          <>
            {/* Top strip */}
            <DailyStrip initialStrip={data.strip} />

            {/* Pillar rows */}
            <div className="mt-4 sm:mt-6">
              <PillarAccordion pillars={data.pillars} />
            </div>
          </>
        )}
      </div>

      <SyncStatusBar status={data.sync_status} today={data.date} />
    </div>
  );
}
