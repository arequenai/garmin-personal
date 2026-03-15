import { format, subDays } from "date-fns";

import { CalorieTrend } from "@/components/nutrition/calorie-trend";
import { MacroDonut } from "@/components/nutrition/macro-donut";
import { NutritionStats } from "@/components/nutrition/nutrition-stats";
import { fetchApi } from "@/lib/api";
import type { NutritionDaily } from "@/lib/types";

export const dynamic = "force-dynamic";

async function getNutritionData(): Promise<NutritionDaily[]> {
  try {
    const toDate = format(new Date(), "yyyy-MM-dd");
    const fromDate = format(subDays(new Date(), 13), "yyyy-MM-dd");
    return await fetchApi<NutritionDaily[]>(
      `/api/nutrition?from_date=${fromDate}&to_date=${toDate}`,
    );
  } catch {
    return [];
  }
}

export default async function NutritionPage() {
  const nutritionData = await getNutritionData();

  // Latest entry is today (API returns desc order)
  const today =
    nutritionData.length > 0 ? nutritionData[0] : null;

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      {/* Header */}
      <div>
        <h1 className="font-heading text-3xl font-bold tracking-tight text-text-primary">
          Nutrition
        </h1>
        <p className="mt-1 text-sm text-text-secondary">
          Calorie &amp; Macro Tracking
        </p>
      </div>

      {/* Charts: Calorie Trend + Macro Donut */}
      <div className="grid gap-4 md:grid-cols-2">
        <CalorieTrend data={nutritionData} />
        <MacroDonut nutrition={today} />
      </div>

      {/* Current Metrics */}
      <NutritionStats nutrition={today} />
    </div>
  );
}
