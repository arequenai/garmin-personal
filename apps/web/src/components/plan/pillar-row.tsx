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
      style={{ borderColor: expanded ? pillar.color : "var(--color-whoop-border)" }}
    >
      {/* Collapsed header — always visible */}
      <button
        onClick={onToggle}
        className="flex w-full items-center justify-between px-3.5 py-2.5"
      >
        <div className="flex items-center gap-2.5">
          <div
            className="h-2.5 w-2.5 rounded-full"
            style={{ background: pillar.color }}
          />
          <span
            className="text-[11px] font-bold tracking-widest"
            style={{ color: pillar.color }}
          >
            {pillar.name.toUpperCase()}
          </span>
        </div>
        <div className="flex items-center gap-5">
          <div className="flex gap-4 text-[11px]">
            {pillar.collapsed_kpis.map((kpi) => (
              <span key={kpi.label}>
                <span className="text-whoop-text-muted">{kpi.label}</span>{" "}
                <span className="font-bold text-whoop-text">{kpi.value}</span>
              </span>
            ))}
          </div>
          <span
            className="text-sm transition-transform"
            style={{
              color: expanded ? pillar.color : "var(--color-whoop-text-muted)",
              transform: expanded ? "rotate(90deg)" : "none",
            }}
          >
            ▸
          </span>
        </div>
      </button>

      {/* Expanded content */}
      {expanded && (
        <div className="border-t border-whoop-border px-3.5 pb-3.5">
          {/* KPI cards with sparklines */}
          <div className="mt-3 grid grid-cols-3 gap-2.5">
            {pillar.expanded_kpis.map((kpi) => (
              <div
                key={kpi.label}
                className="rounded-lg bg-whoop-surface p-2.5"
              >
                <div className="text-[9px] uppercase tracking-wider text-whoop-text-muted">
                  {kpi.label}
                </div>
                <div className="mt-1 flex items-baseline gap-1.5">
                  <span className="text-lg font-extrabold text-whoop-text">
                    {kpi.value}
                  </span>
                  {kpi.target && (
                    <span className="text-[10px] text-whoop-text-muted">
                      target {kpi.target}
                    </span>
                  )}
                </div>
                {kpi.spark.length > 1 && (
                  <div className="mt-1.5">
                    <Sparkline7d data={kpi.spark} color={pillar.color} />
                    <div className="text-right text-[8px] text-whoop-text-muted">
                      7d trend
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Drivers */}
          {pillar.drivers.length > 0 && (
            <div className="mt-2.5 flex gap-2">
              {pillar.drivers.map((d) => (
                <div
                  key={d.label}
                  className="flex flex-1 items-center justify-between rounded-md bg-whoop-surface px-2 py-1.5"
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
