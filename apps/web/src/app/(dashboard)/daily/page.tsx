import { DM_Sans } from "next/font/google";
import { fetchApi } from "@/lib/api";
import { emptyOverviewData, type OverviewData } from "@/lib/types";
import { DailyClient } from "@/components/overview/daily-client";

export const dynamic = "force-dynamic";

const dmSans = DM_Sans({ subsets: ["latin"], variable: "--font-dm-sans" });

export default async function DailyPage() {
  let data: OverviewData;
  try {
    data = await fetchApi<OverviewData>("/api/overview");
  } catch {
    data = emptyOverviewData();
  }

  return (
    <div className={dmSans.variable}>
      <DailyClient data={data} />
    </div>
  );
}
