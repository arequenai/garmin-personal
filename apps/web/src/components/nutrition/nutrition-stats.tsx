import { Beef, Flame, Wheat, Droplets } from "lucide-react";

import { MetricCard } from "@/components/ui/metric-card";
import type { NutritionDaily } from "@/lib/types";
import { formatNumber } from "@/lib/format";

interface NutritionStatsProps {
  nutrition: NutritionDaily | null;
}

export function NutritionStats({ nutrition }: NutritionStatsProps) {
  return (
    <div>
      <h2 className="mb-3 text-sm font-medium text-text-secondary">
        Current Metrics
      </h2>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <MetricCard
          label="Calories"
          value={
            nutrition?.calories != null
              ? formatNumber(nutrition.calories)
              : "--"
          }
          unit="kcal"
          icon={<Flame size={18} />}
          accentColor="text-strain"
        />
        <MetricCard
          label="Protein"
          value={
            nutrition?.protein_g != null
              ? Math.round(nutrition.protein_g).toString()
              : "--"
          }
          unit="g"
          icon={<Beef size={18} />}
          accentColor="text-sleep"
        />
        <MetricCard
          label="Carbs"
          value={
            nutrition?.carbs_g != null
              ? Math.round(nutrition.carbs_g).toString()
              : "--"
          }
          unit="g"
          icon={<Wheat size={18} />}
          accentColor="text-strain"
        />
        <MetricCard
          label="Fat"
          value={
            nutrition?.fat_g != null
              ? Math.round(nutrition.fat_g).toString()
              : "--"
          }
          unit="g"
          icon={<Droplets size={18} />}
          accentColor="text-alert"
        />
      </div>
    </div>
  );
}
