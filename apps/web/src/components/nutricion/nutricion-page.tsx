"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { useNutritionData } from "@/lib/hooks/use-nutrition-data";
import { useBodyComposition } from "@/lib/hooks/use-body-composition";
import { CaloriesChart } from "./calories-chart";
import { MacroStackedChart } from "./macro-stacked-chart";
import { AlcoholStrip } from "./alcohol-strip";
import { WeightBFChart } from "./weight-bf-chart";

function defaultFrom(monthsBack: number): string {
  const d = new Date();
  d.setMonth(d.getMonth() - monthsBack);
  return d.toISOString().split("T")[0];
}

function defaultFromWeeks(weeksBack: number): string {
  const d = new Date();
  d.setDate(d.getDate() - weeksBack * 7);
  return d.toISOString().split("T")[0];
}

function today(): string {
  return new Date().toISOString().split("T")[0];
}

const PRESETS = [
  { label: "1W", weeks: 1, months: undefined },
  { label: "1M", weeks: undefined, months: 1 },
  { label: "3M", weeks: undefined, months: 3 },
  { label: "6M", weeks: undefined, months: 6 },
  { label: "1Y", weeks: undefined, months: 12 },
];

function ChartError({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-8">
      <p className="text-xs text-whoop-text-muted">Could not load data</p>
      <button onClick={onRetry} className="mt-2 text-xs text-whoop-blue hover:underline">
        Retry
      </button>
    </div>
  );
}

function ChartSkeleton({ height = "h-[200px]" }: { height?: string }) {
  return (
    <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
      <div className={`${height} animate-pulse rounded bg-whoop-surface`} />
    </div>
  );
}

export function NutricionPageClient() {
  const [from, setFrom] = useState(() => defaultFrom(1));
  const [to, setTo] = useState(today);
  const [activePreset, setActivePreset] = useState("1M");

  const nutrition = useNutritionData(from, to);
  const bodyComp = useBodyComposition(from, to);

  const applyPreset = (preset: (typeof PRESETS)[number]) => {
    const newFrom = preset.weeks
      ? defaultFromWeeks(preset.weeks)
      : defaultFrom(preset.months!);
    setFrom(newFrom);
    setTo(today());
    setActivePreset(preset.label);
  };

  return (
    <div className="min-h-screen bg-whoop-bg text-whoop-text">
      <div className="mx-auto max-w-6xl px-3 pt-4 pb-20 sm:px-6 sm:pt-6 sm:pb-16">
        {/* Header bar */}
        <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <Link
            href="/"
            className="flex items-center gap-1.5 text-sm text-whoop-text-muted hover:text-whoop-text transition-colors"
          >
            <ArrowLeft size={16} />
            Plan
          </Link>

          <div className="flex items-center gap-2">
            {PRESETS.map((p) => (
              <button
                key={p.label}
                onClick={() => applyPreset(p)}
                className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                  activePreset === p.label
                    ? "bg-whoop-surface text-whoop-text"
                    : "text-whoop-text-muted hover:bg-whoop-surface/50"
                }`}
              >
                {p.label}
              </button>
            ))}
            <input
              type="date"
              value={from}
              onChange={(e) => {
                setFrom(e.target.value);
                setActivePreset("");
              }}
              className="rounded-md border border-whoop-border bg-whoop-surface px-2 py-1 text-xs text-whoop-text"
            />
            <input
              type="date"
              value={to}
              onChange={(e) => {
                setTo(e.target.value);
                setActivePreset("");
              }}
              className="rounded-md border border-whoop-border bg-whoop-surface px-2 py-1 text-xs text-whoop-text"
            />
          </div>
        </div>

        {/* Main grid: charts left, summary right */}
        <div className="flex flex-col gap-4 md:flex-row">
          {/* Left: charts */}
          <div className="flex flex-1 flex-col gap-4 md:w-3/4">
            {nutrition.loading ? (
              <>
                <ChartSkeleton height="h-[200px]" />
                <ChartSkeleton height="h-[120px]" />
                <ChartSkeleton height="h-[40px]" />
              </>
            ) : nutrition.error ? (
              <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
                <ChartError onRetry={() => setFrom((f) => f)} />
              </div>
            ) : (
              <>
                {/* Calories chart — Task 7 */}
                <CaloriesChart data={nutrition.data!} />
                {/* Macro chart — Task 8 */}
                <MacroStackedChart data={nutrition.data!} />
                {/* Alcohol strip — Task 9 */}
                <AlcoholStrip data={nutrition.data!} />
              </>
            )}

            {/* Weight/BF chart */}
            {bodyComp.loading ? (
              <ChartSkeleton height="h-[200px]" />
            ) : bodyComp.error ? (
              <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
                <ChartError onRetry={() => setFrom((f) => f)} />
              </div>
            ) : (
              <WeightBFChart data={bodyComp.data!} />
            )}
          </div>

          {/* Right: summary sidebar — Task 11 */}
          <div className="flex flex-col gap-4 md:w-1/4">
            <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
              <p className="text-xs text-whoop-text-muted">Summary sidebar placeholder</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
