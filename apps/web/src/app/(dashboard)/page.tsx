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
      <div className="sticky top-0 z-50 flex items-center justify-between border-b border-whoop-border bg-whoop-bg/90 px-4 py-3 backdrop-blur-xl sm:px-6">
        <div>
          <div
            className="text-base font-extrabold tracking-tight sm:text-lg"
            style={{ fontFamily: "'DM Sans', sans-serif" }}
          >
            <span className="text-whoop-green">P</span>LAN ESTRATÉGICO
          </div>
          <div className="text-[10px] tracking-wider text-whoop-text-muted sm:text-[11px]">
            {dateStr.toUpperCase()}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="mx-auto max-w-[1200px] px-3 py-4 pb-20 sm:px-6 sm:py-6 sm:pb-16">
        {/* Top strip */}
        <DailyStrip initialStrip={data.strip} />

        {/* Pillar rows */}
        <div className="mt-4 sm:mt-6">
          <PillarAccordion pillars={data.pillars} />
        </div>
      </div>
    </div>
  );
}
