"use client";

import { useEffect, useState } from "react";
import type { StripMetric, PlanDailyData } from "@/lib/types";
import { fetchApi } from "@/lib/api";

function TrendArrow({ trend }: { trend: string | null }) {
  if (!trend || trend === "flat") return null;
  const color = trend === "up" ? "text-green-400" : "text-red-400";
  const arrow = trend === "up" ? "↑" : "↓";
  return <span className={`ml-1 text-xs ${color}`}>{arrow}</span>;
}

function MetricCard({ metric }: { metric: StripMetric }) {
  const hasProgress = metric.pct != null && metric.target;

  return (
    <div className="rounded-xl border border-whoop-border bg-whoop-card p-3 text-center">
      <div className="text-[9px] font-semibold uppercase tracking-wider text-whoop-text-muted">
        {metric.label}
      </div>
      <div className="mt-1.5">
        <span className="text-xl font-extrabold text-whoop-text">{metric.value}</span>
        <TrendArrow trend={metric.trend} />
        {metric.target && (
          <>
            <span className="mx-1 text-xs text-whoop-text-muted">/</span>
            <span className="text-sm text-whoop-text-secondary">{metric.target}</span>
          </>
        )}
      </div>
      <div className="text-[9px] text-whoop-text-muted">{metric.unit}</div>
      {hasProgress && (
        <div className="mx-auto mt-1.5 h-[3px] w-full rounded-full bg-whoop-surface">
          <div
            className="h-[3px] rounded-full bg-whoop-green"
            style={{ width: `${Math.min(metric.pct!, 100)}%` }}
          />
        </div>
      )}
      {metric.secondary_value && (
        <div className="mt-1 text-[9px] text-whoop-text-secondary">
          {metric.secondary_value}
        </div>
      )}
    </div>
  );
}

interface DailyStripProps {
  initialStrip: StripMetric[];
}

export function DailyStrip({ initialStrip }: DailyStripProps) {
  const [strip, setStrip] = useState(initialStrip);

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const data = await fetchApi<PlanDailyData>("/api/plan/daily");
        setStrip(data.strip);
      } catch {
        // Keep showing stale data on fetch failure
      }
    }, 60_000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="grid grid-cols-6 gap-2">
      {strip.map((m) => (
        <MetricCard key={m.label} metric={m} />
      ))}
    </div>
  );
}
