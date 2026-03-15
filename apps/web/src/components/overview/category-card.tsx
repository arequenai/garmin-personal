"use client";

import type { OverviewCategory } from "@/lib/types";
import { Ring } from "./ring";
import { Sparkline } from "./sparkline";
import { TrendBadge } from "./trend-badge";

const INVERT_LABELS = new Set([
  "RHR", "Body Fat", "Max Glucose", "Variability", "Fat Weight", "BMI",
  "Marathon Time", "Fasting Glucose",
]);

interface CategoryCardProps {
  category: OverviewCategory;
  label: string;
  icon: string;
  color: string;
}

export function CategoryCard({ category, label, icon, color }: CategoryCardProps) {
  return (
    <div className="flex flex-col gap-5 rounded-2xl border border-whoop-border bg-whoop-card p-6">
      {/* Header */}
      <span
        className="text-lg font-bold uppercase tracking-widest"
        style={{ color, fontFamily: "'DM Sans', sans-serif" }}
      >
        {label}
      </span>

      {/* Key indicator + ring + sparkline */}
      <div className="flex items-center gap-5">
        <Ring size={100} stroke={7} pct={category.score ?? 0} color={color}>
          <span
            className="text-[22px] font-extrabold text-whoop-text"
            style={{ fontFamily: "'DM Sans', sans-serif" }}
          >
            {category.score ?? "--"}
          </span>
        </Ring>

        {category.key_indicator && (
          <div className="flex-1">
            <div className="mb-1 text-[11px] uppercase tracking-wider text-whoop-text-muted">
              {category.key_indicator.label}
            </div>
            <div className="flex items-baseline gap-2">
              <span
                className="text-[28px] font-extrabold text-whoop-text"
                style={{ fontFamily: "'DM Sans', sans-serif" }}
              >
                {category.key_indicator.value}
              </span>
              <span className="text-xs text-whoop-text-secondary">
                {category.key_indicator.unit}
              </span>
            </div>
            <TrendBadge
              value={category.key_indicator.trend_pct}
              invert={INVERT_LABELS.has(category.key_indicator.label)}
            />
          </div>
        )}

        {category.key_indicator?.spark && category.key_indicator.spark.length > 1 && (
          <div className="shrink-0">
            <Sparkline data={category.key_indicator.spark} color={color} width={80} height={36} />
          </div>
        )}
      </div>

      {/* KPIs */}
      {category.kpis.length > 0 && (
        <div className="grid grid-cols-3 gap-3">
          {category.kpis.map((kpi) => (
            <div key={kpi.label} className="rounded-xl bg-whoop-surface px-3 py-2.5">
              <div className="mb-1 text-[10px] uppercase tracking-wider text-whoop-text-muted">
                {kpi.label}
              </div>
              <div
                className="text-base font-bold text-whoop-text"
                style={{ fontFamily: "'DM Sans', sans-serif" }}
              >
                {kpi.value}
                <span className="ml-1 text-[10px] text-whoop-text-secondary">{kpi.unit}</span>
              </div>
              <TrendBadge value={kpi.trend_pct} invert={INVERT_LABELS.has(kpi.label)} />
            </div>
          ))}
        </div>
      )}

      {/* Drivers */}
      {category.drivers.length > 0 && (
        <div className="border-t border-whoop-border pt-3.5">
          <div className="mb-2.5 text-[10px] uppercase tracking-widest text-whoop-text-muted">
            Drivers
          </div>
          <div className="grid grid-cols-3 gap-2">
            {category.drivers.map((d) => (
              <div key={d.label} className="flex flex-col gap-1 rounded-lg bg-whoop-surface px-2.5 py-2">
                <div className="text-[9px] uppercase tracking-wider text-whoop-text-muted">
                  {d.label}
                </div>
                <div className="flex items-baseline gap-1">
                  <span
                    className="text-sm font-bold"
                    style={{ color, fontFamily: "'DM Sans', sans-serif" }}
                  >
                    {d.value}
                  </span>
                  <span className="text-[9px] text-whoop-text-secondary">{d.unit}</span>
                </div>
                <TrendBadge value={d.trend_pct} />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
