"use client";

import type { PillarData } from "@/lib/types";
import { Sparkline7d } from "./sparkline-7d";

interface PillarRowProps {
  pillar: PillarData;
  expanded: boolean;
  onToggle: () => void;
}

export function PillarRow({ pillar, expanded, onToggle }: PillarRowProps) {
  return (
    <div
      className="overflow-hidden rounded-xl border transition-colors"
      style={{
        borderColor: expanded ? pillar.color : "var(--color-whoop-border)",
      }}
    >
      {/* Collapsed header — always visible */}
      <button
        onClick={onToggle}
        className="flex w-full items-center justify-between gap-2 px-3 py-2.5 sm:px-3.5"
      >
        <div className="flex min-w-0 items-center gap-2">
          <div
            className="h-2.5 w-2.5 shrink-0 rounded-full"
            style={{ background: pillar.color }}
          />
          <span
            className="truncate text-[10px] font-bold tracking-widest sm:text-[11px]"
            style={{ color: pillar.color }}
          >
            {pillar.name.toUpperCase()}
          </span>
        </div>
        <div className="flex shrink-0 items-center gap-3 sm:gap-5">
          <div className="hidden gap-4 text-[11px] sm:flex">
            {pillar.collapsed_kpis.map((kpi) => (
              <span key={kpi.label}>
                <span className="text-whoop-text-muted">{kpi.label}</span>{" "}
                <span className="font-bold text-whoop-text">{kpi.value}</span>
              </span>
            ))}
          </div>
          {/* Mobile: show only values */}
          <div className="flex gap-3 text-[10px] sm:hidden">
            {pillar.collapsed_kpis.map((kpi) => (
              <span key={kpi.label} className="font-bold text-whoop-text">
                {kpi.value}
              </span>
            ))}
          </div>
          <span
            className="text-sm transition-transform"
            style={{
              color: expanded
                ? pillar.color
                : "var(--color-whoop-text-muted)",
              transform: expanded ? "rotate(90deg)" : "none",
            }}
          >
            &#9656;
          </span>
        </div>
      </button>

      {/* Expanded content */}
      {expanded && (
        <div className="border-t border-whoop-border px-3 pb-3 sm:px-3.5 sm:pb-3.5">
          {/* KPI cards with sparklines */}
          <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-3 sm:gap-2.5">
            {pillar.expanded_kpis.map((kpi) => (
              <div key={kpi.label} className="rounded-lg bg-whoop-surface p-2.5">
                <div className="flex items-center justify-between sm:block">
                  <div>
                    <div className="text-[9px] uppercase tracking-wider text-whoop-text-muted">
                      {kpi.label}
                    </div>
                    <div className="mt-0.5 flex items-baseline gap-1.5 sm:mt-1">
                      <span className="text-lg font-extrabold text-whoop-text">
                        {kpi.value}
                      </span>
                      {kpi.target && (
                        <span className="text-[10px] text-whoop-text-muted">
                          target {kpi.target}
                        </span>
                      )}
                    </div>
                  </div>
                  {kpi.spark.length > 1 && (
                    <div className="w-20 sm:mt-1.5 sm:w-auto">
                      <Sparkline7d data={kpi.spark} color={pillar.color} />
                      <div className="text-right text-[8px] text-whoop-text-muted">
                        7d trend
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Drivers */}
          {pillar.drivers.length > 0 && (
            <div className="mt-2.5 grid grid-cols-2 gap-1.5 sm:flex sm:gap-2">
              {pillar.drivers.map((d) => (
                <div
                  key={d.label}
                  className="flex items-center justify-between rounded-md bg-whoop-surface px-2 py-1.5 sm:flex-1"
                >
                  <span className="text-[9px] text-whoop-text-muted">
                    {d.label}
                  </span>
                  <span
                    className="text-[11px] font-bold"
                    style={{ color: pillar.color }}
                  >
                    {d.value}
                    {d.unit && (
                      <span className="ml-0.5 text-[8px] text-whoop-text-secondary">
                        {d.unit}
                      </span>
                    )}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
