"use client";

import { useMemo } from "react";
import type { NutritionDay, BodyCompositionDay } from "@/lib/types";

interface SummarySidebarProps {
  nutrition: NutritionDay[];
  bodyComp: BodyCompositionDay[];
}

const ALCOHOL_LIMIT = 3;

function getISOWeekKey(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  d.setDate(d.getDate() + 3 - ((d.getDay() + 6) % 7));
  const yearStart = new Date(d.getFullYear(), 0, 4);
  const weekNo = Math.ceil(
    ((d.getTime() - yearStart.getTime()) / 86400000 + yearStart.getDay() + 1) / 7,
  );
  return `${d.getFullYear()}-W${String(weekNo).padStart(2, "0")}`;
}

function getCurrentISOWeekKey(): string {
  return getISOWeekKey(new Date().toISOString().split("T")[0]);
}

function alcoholColor(count: number): string {
  if (count >= ALCOHOL_LIMIT) return "#ef4444";
  if (count === 2) return "#eab308";
  return "#00d68f";
}

export function SummarySidebar({ nutrition, bodyComp }: SummarySidebarProps) {
  const stats = useMemo(() => {
    const withCal = nutrition.filter((d) => d.calories != null);
    const avgCal =
      withCal.length > 0
        ? Math.round(withCal.reduce((s, d) => s + d.calories!, 0) / withCal.length)
        : null;

    const goals = withCal.filter((d) => d.calories_goal != null);
    const avgGoal =
      goals.length > 0
        ? Math.round(goals.reduce((s, d) => s + d.calories_goal!, 0) / goals.length)
        : null;

    const onTarget =
      avgGoal != null
        ? withCal.filter((d) => d.calories! <= (d.calories_goal ?? Infinity)).length
        : 0;
    const pctOnTarget = withCal.length > 0 ? Math.round((onTarget / withCal.length) * 100) : 0;
    const avgDeficit = avgCal != null && avgGoal != null ? avgCal - avgGoal : null;

    // Macros
    const withMacros = nutrition.filter(
      (d) => d.protein_g != null && d.carbs_g != null && d.fat_g != null,
    );
    const avgProtein =
      withMacros.length > 0
        ? Math.round(withMacros.reduce((s, d) => s + d.protein_g!, 0) / withMacros.length)
        : null;
    const avgCarbs =
      withMacros.length > 0
        ? Math.round(withMacros.reduce((s, d) => s + d.carbs_g!, 0) / withMacros.length)
        : null;
    const avgFat =
      withMacros.length > 0
        ? Math.round(withMacros.reduce((s, d) => s + d.fat_g!, 0) / withMacros.length)
        : null;
    const macroTotal = (avgProtein ?? 0) + (avgCarbs ?? 0) + (avgFat ?? 0);
    const proteinPct = macroTotal > 0 ? Math.round(((avgProtein ?? 0) / macroTotal) * 100) : 0;
    const carbsPct = macroTotal > 0 ? Math.round(((avgCarbs ?? 0) / macroTotal) * 100) : 0;
    const fatPct = macroTotal > 0 ? Math.round(((avgFat ?? 0) / macroTotal) * 100) : 0;

    // Alcohol by week
    const weekMap = new Map<string, number>();
    for (const d of nutrition) {
      if (d.alcohol_drinks == null) continue;
      const wk = getISOWeekKey(d.date);
      weekMap.set(wk, (weekMap.get(wk) ?? 0) + d.alcohol_drinks);
    }
    const weeks = [...weekMap.entries()].sort((a, b) => a[0].localeCompare(b[0]));
    const currentWeekKey = getCurrentISOWeekKey();
    const currentWeekDrinks = weekMap.get(currentWeekKey) ?? 0;
    const weeksUnderLimit = weeks.filter(([, c]) => c < ALCOHOL_LIMIT).length;

    // Body comp
    const sortedBC = [...bodyComp]
      .filter((d) => d.weight_kg != null || d.body_fat_pct != null)
      .sort((a, b) => a.date.localeCompare(b.date));
    const firstBC = sortedBC[0];
    const lastBC = sortedBC[sortedBC.length - 1];
    const currentWeight = lastBC?.weight_kg ?? null;
    const currentBF = lastBC?.body_fat_pct ?? null;
    const weightDelta =
      firstBC?.weight_kg != null && lastBC?.weight_kg != null
        ? lastBC.weight_kg - firstBC.weight_kg
        : null;
    const bfDelta =
      firstBC?.body_fat_pct != null && lastBC?.body_fat_pct != null
        ? lastBC.body_fat_pct - firstBC.body_fat_pct
        : null;

    return {
      avgCal,
      avgGoal,
      avgDeficit,
      pctOnTarget,
      totalDays: withCal.length,
      avgProtein,
      avgCarbs,
      avgFat,
      proteinPct,
      carbsPct,
      fatPct,
      currentWeekDrinks,
      weeks,
      weeksUnderLimit,
      currentWeight,
      currentBF,
      weightDelta,
      bfDelta,
    };
  }, [nutrition, bodyComp]);

  return (
    <div className="flex flex-col gap-4">
      {/* Calories */}
      <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
        <p className="mb-2 text-[9px] uppercase tracking-wider text-whoop-text-muted">Calories</p>
        <p className="text-2xl font-bold text-whoop-text">
          {stats.avgCal != null ? stats.avgCal.toLocaleString() : "--"}
        </p>
        <p className="text-xs text-whoop-text-muted">avg/day</p>

        {stats.avgDeficit != null && (
          <div className="mt-3 border-t border-whoop-border pt-3">
            <p className="text-[9px] text-whoop-text-muted">
              vs goal ({stats.avgGoal?.toLocaleString()})
            </p>
            <p
              className={`text-sm font-bold ${stats.avgDeficit <= 0 ? "text-green-400" : "text-red-400"}`}
            >
              {stats.avgDeficit > 0 ? "+" : ""}
              {stats.avgDeficit}
            </p>
            <p className="text-xs text-whoop-text-muted">
              avg {stats.avgDeficit <= 0 ? "deficit" : "surplus"}
            </p>
          </div>
        )}

        <div className="mt-3 border-t border-whoop-border pt-3">
          <div className="flex items-center justify-between">
            <span className="text-[9px] text-whoop-text-muted">Days on target</span>
            <span className="text-xs font-bold text-green-400">{stats.pctOnTarget}%</span>
          </div>
          <div className="mt-1 h-1 rounded-full bg-whoop-surface">
            <div
              className="h-1 rounded-full bg-green-400"
              style={{ width: `${stats.pctOnTarget}%` }}
            />
          </div>
        </div>
      </div>

      {/* Macros */}
      <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
        <p className="mb-2 text-[9px] uppercase tracking-wider text-whoop-text-muted">Avg Macros</p>
        <div className="space-y-2">
          {[
            { label: "Protein", g: stats.avgProtein, pct: stats.proteinPct, color: "#4da6ff" },
            { label: "Carbs", g: stats.avgCarbs, pct: stats.carbsPct, color: "#00d68f" },
            { label: "Fat", g: stats.avgFat, pct: stats.fatPct, color: "#f97316" },
          ].map((m) => (
            <div key={m.label}>
              <div className="flex items-baseline justify-between">
                <span className="text-sm font-bold" style={{ color: m.color }}>
                  {m.g != null ? `${m.g}g` : "--"}
                </span>
                <span className="text-[9px] text-whoop-text-muted">{m.pct}%</span>
              </div>
              <p className="text-[9px] text-whoop-text-muted">{m.label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Alcohol */}
      <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
        <p className="mb-2 text-[9px] uppercase tracking-wider text-whoop-text-muted">Alcohol</p>
        <div className="flex items-baseline gap-1">
          <span
            className="text-2xl font-bold"
            style={{ color: alcoholColor(stats.currentWeekDrinks) }}
          >
            {stats.currentWeekDrinks}
          </span>
          <span className="text-xs text-whoop-text-muted">/ {ALCOHOL_LIMIT} this week</span>
        </div>

        {stats.weeks.length > 0 && (
          <div className="mt-3 border-t border-whoop-border pt-3">
            <div className="flex items-center justify-between">
              <span className="text-[9px] text-whoop-text-muted">Weeks in range</span>
              <span className="text-xs font-bold text-green-400">
                {stats.weeksUnderLimit}/{stats.weeks.length}
              </span>
            </div>
            <div className="mt-2 flex flex-wrap gap-1">
              {stats.weeks.map(([wk, count]) => (
                <div
                  key={wk}
                  className="flex h-5 w-5 items-center justify-center rounded text-[8px] font-bold"
                  style={{
                    backgroundColor: alcoholColor(count),
                    color: count >= ALCOHOL_LIMIT ? "#fff" : "#000",
                  }}
                  title={`${wk}: ${count} drinks`}
                >
                  {count}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Body comp */}
      <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
        <p className="mb-2 text-[9px] uppercase tracking-wider text-whoop-text-muted">Body Comp</p>
        <div className="space-y-3">
          <div>
            <div className="flex items-baseline justify-between">
              <span className="text-lg font-bold text-whoop-text">
                {stats.currentWeight != null ? stats.currentWeight.toFixed(1) : "--"}
              </span>
              {stats.weightDelta != null && (
                <span
                  className={`text-xs ${stats.weightDelta <= 0 ? "text-green-400" : "text-red-400"}`}
                >
                  {stats.weightDelta > 0 ? "↑" : "↓"} {Math.abs(stats.weightDelta).toFixed(1)} kg
                </span>
              )}
            </div>
            <p className="text-[9px] text-whoop-text-muted">Weight (kg)</p>
          </div>
          <div>
            <div className="flex items-baseline justify-between">
              <span className="text-lg font-bold text-whoop-text">
                {stats.currentBF != null ? stats.currentBF.toFixed(1) : "--"}
              </span>
              {stats.bfDelta != null && (
                <span
                  className={`text-xs ${stats.bfDelta <= 0 ? "text-green-400" : "text-red-400"}`}
                >
                  {stats.bfDelta > 0 ? "↑" : "↓"} {Math.abs(stats.bfDelta).toFixed(1)}%
                </span>
              )}
            </div>
            <p className="text-[9px] text-whoop-text-muted">Body Fat (%)</p>
          </div>
        </div>
      </div>
    </div>
  );
}
