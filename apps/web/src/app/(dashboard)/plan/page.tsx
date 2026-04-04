import { DM_Sans } from "next/font/google";
import { fetchApi } from "@/lib/api";
import { emptyPlanDailyData, type PlanDailyData } from "@/lib/types";
import { DailyStrip } from "@/components/plan/daily-strip";
import { PillarAccordion } from "@/components/plan/pillar-accordion";

export const dynamic = "force-dynamic";

const dmSans = DM_Sans({ subsets: ["latin"], variable: "--font-dm-sans" });

export default async function PlanPage() {
  let data: PlanDailyData;
  try {
    data = await fetchApi<PlanDailyData>("/api/plan/daily");
  } catch {
    data = emptyPlanDailyData();
  }

  const today = new Date();
  const dateStr = today.toLocaleDateString("en-US", {
    weekday: "long",
    month: "short",
    day: "numeric",
  });

  return (
    <div className={`${dmSans.variable} min-h-screen bg-whoop-bg text-whoop-text`}>
      {/* Header */}
      <div className="sticky top-0 z-50 flex items-center justify-between border-b border-whoop-border bg-whoop-bg/90 px-6 py-3 backdrop-blur-xl">
        <div>
          <div
            className="text-lg font-extrabold tracking-tight"
            style={{ fontFamily: "'DM Sans', sans-serif" }}
          >
            <span className="text-whoop-green">P</span>LAN ESTRATÉGICO
          </div>
          <div className="text-[11px] tracking-wider text-whoop-text-muted">
            {dateStr.toUpperCase()}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="mx-auto max-w-[1200px] px-6 py-6 pb-16">
        {/* Top strip */}
        <DailyStrip initialStrip={data.strip} />

        {/* Pillar rows */}
        <div className="mt-6">
          <PillarAccordion pillars={data.pillars} />
        </div>
      </div>
    </div>
  );
}
