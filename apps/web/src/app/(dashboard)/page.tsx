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

  return (
    <div className={`${dmSans.variable} min-h-screen bg-whoop-bg text-whoop-text`}>
      {/* Content */}
      <div className="mx-auto max-w-[1200px] px-3 pt-4 pb-20 sm:px-6 sm:pt-6 sm:pb-16">
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
