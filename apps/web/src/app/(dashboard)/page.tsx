import { DM_Sans } from "next/font/google";
import { fetchApi } from "@/lib/api";
import type { OverviewData } from "@/lib/types";
import { OverviewClient } from "@/components/overview/overview-client";

export const dynamic = "force-dynamic";

const dmSans = DM_Sans({ subsets: ["latin"], variable: "--font-dm-sans" });

export default async function OverviewPage() {
  let data: OverviewData;
  try {
    data = await fetchApi<OverviewData>("/api/overview");
  } catch {
    data = {
      date: new Date().toISOString().split("T")[0],
      categories: {
        running: { score: null, key_indicator: null, kpis: [], drivers: [] },
        strength: { score: null, key_indicator: null, kpis: [], drivers: [] },
        recovery: { score: null, key_indicator: null, kpis: [], drivers: [] },
        sleep: { score: null, key_indicator: null, kpis: [], drivers: [] },
        body: { score: null, key_indicator: null, kpis: [], drivers: [] },
        glucose: { score: null, key_indicator: null, kpis: [], drivers: [] },
      },
      daily_sections: [],
    };
  }

  return (
    <div className={dmSans.variable}>
      <OverviewClient data={data} />
    </div>
  );
}
