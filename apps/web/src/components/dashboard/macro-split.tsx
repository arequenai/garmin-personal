import type { NutritionDaily } from "@/lib/types";
import { formatNumber } from "@/lib/format";

interface MacroSplitProps {
  nutrition: NutritionDaily | null;
  calorieGoal?: number;
}

export function MacroSplit({ nutrition, calorieGoal }: MacroSplitProps) {
  if (!nutrition || nutrition.calories == null) {
    return (
      <div className="rounded-2xl bg-bg-card p-6">
        <span className="text-sm font-medium tracking-wide text-text-secondary uppercase">
          Macros Today
        </span>
        <p className="mt-4 text-sm text-text-secondary">
          No nutrition data &mdash; connect MyFitnessPal
        </p>
      </div>
    );
  }

  const protein = nutrition.protein_g ?? 0;
  const carbs = nutrition.carbs_g ?? 0;
  const fat = nutrition.fat_g ?? 0;
  const total = protein + carbs + fat;

  // Percentages for the stacked bar
  const pPct = total > 0 ? (protein / total) * 100 : 0;
  const cPct = total > 0 ? (carbs / total) * 100 : 0;
  const fPct = total > 0 ? (fat / total) * 100 : 0;

  return (
    <div className="rounded-2xl bg-bg-card p-6">
      <span className="text-sm font-medium tracking-wide text-text-secondary uppercase">
        Macros Today
      </span>

      {/* Stacked bar */}
      <div className="mt-4 flex h-3 w-full overflow-hidden rounded-full bg-bg-hover">
        {pPct > 0 && (
          <div
            className="h-full rounded-l-full bg-blue-500 transition-[width] duration-500"
            style={{ width: `${pPct}%` }}
          />
        )}
        {cPct > 0 && (
          <div
            className="h-full bg-amber-500 transition-[width] duration-500"
            style={{ width: `${cPct}%` }}
          />
        )}
        {fPct > 0 && (
          <div
            className="h-full rounded-r-full bg-rose-500 transition-[width] duration-500"
            style={{ width: `${fPct}%` }}
          />
        )}
      </div>

      {/* Legend */}
      <div className="mt-4 flex flex-wrap items-center gap-5 text-sm">
        <MacroLabel color="bg-blue-500" label="Protein" grams={protein} />
        <MacroLabel color="bg-amber-500" label="Carbs" grams={carbs} />
        <MacroLabel color="bg-rose-500" label="Fat" grams={fat} />
      </div>

      {/* Calorie total */}
      <p className="mt-3 text-sm text-text-secondary">
        Calories:{" "}
        <span className="font-medium text-text-primary">
          {formatNumber(nutrition.calories)}
        </span>
        {calorieGoal != null && (
          <span> / {formatNumber(calorieGoal)}</span>
        )}
      </p>
    </div>
  );
}

function MacroLabel({
  color,
  label,
  grams,
}: {
  color: string;
  label: string;
  grams: number;
}) {
  return (
    <div className="flex items-center gap-1.5">
      <span className={`inline-block h-2.5 w-2.5 rounded-full ${color}`} />
      <span className="text-text-secondary">
        {label[0]}:{" "}
        <span className="font-medium text-text-primary">
          {Math.round(grams)}g
        </span>
      </span>
    </div>
  );
}
