"use client";

import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";

import type { NutritionDaily } from "@/lib/types";
import { formatNumber } from "@/lib/format";

interface MacroDonutProps {
  nutrition: NutritionDaily | null;
}

interface MacroSegment {
  name: string;
  grams: number;
  color: string;
}

const MACRO_COLORS = {
  Protein: "#6366f1",
  Carbs: "#f59e0b",
  Fat: "#ec4899",
} as const;

export function MacroDonut({ nutrition }: MacroDonutProps) {
  if (!nutrition || nutrition.calories == null) {
    return (
      <div className="rounded-2xl bg-bg-card p-6">
        <h2 className="font-heading text-lg font-semibold text-text-primary">
          Today&apos;s Macros
        </h2>
        <div className="flex h-[300px] items-center justify-center text-text-secondary">
          No nutrition data available
        </div>
      </div>
    );
  }

  const protein = nutrition.protein_g ?? 0;
  const carbs = nutrition.carbs_g ?? 0;
  const fat = nutrition.fat_g ?? 0;
  const totalGrams = protein + carbs + fat;
  const totalCalories = nutrition.calories;

  const segments: MacroSegment[] = [
    { name: "Protein", grams: protein, color: MACRO_COLORS.Protein },
    { name: "Carbs", grams: carbs, color: MACRO_COLORS.Carbs },
    { name: "Fat", grams: fat, color: MACRO_COLORS.Fat },
  ];

  const pctOf = (g: number) =>
    totalGrams > 0 ? Math.round((g / totalGrams) * 100) : 0;

  return (
    <div className="rounded-2xl bg-bg-card p-6">
      <h2 className="mb-4 font-heading text-lg font-semibold text-text-primary">
        Today&apos;s Macros
      </h2>

      {/* Donut chart with center label */}
      <div className="relative">
        <ResponsiveContainer width="100%" height={220}>
          <PieChart>
            <Pie
              data={segments}
              dataKey="grams"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={90}
              paddingAngle={3}
              stroke="none"
            >
              {segments.map((seg) => (
                <Cell key={seg.name} fill={seg.color} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>

        {/* Center label */}
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-heading text-3xl font-bold text-text-primary">
            {formatNumber(totalCalories)}
          </span>
          <span className="text-xs text-text-secondary">kcal</span>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-2 flex flex-col gap-2">
        {segments.map((seg) => (
          <div
            key={seg.name}
            className="flex items-center justify-between text-sm"
          >
            <div className="flex items-center gap-2">
              <span
                className="inline-block h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: seg.color }}
              />
              <span className="text-text-secondary">{seg.name}</span>
            </div>
            <span className="font-medium text-text-primary">
              {Math.round(seg.grams)}g{" "}
              <span className="text-text-secondary">({pctOf(seg.grams)}%)</span>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
