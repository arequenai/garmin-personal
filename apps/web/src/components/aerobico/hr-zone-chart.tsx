"use client";

import type { HRZonesData, WeeklyHRZones } from "@/lib/types";

interface HRZoneChartProps {
  data: HRZonesData;
}

const ZONES = [
  { key: "zone1_sec" as const, label: "Z1", color: "#6b7280", name: "Recovery" },
  { key: "zone2_sec" as const, label: "Z2", color: "#4da6ff", name: "Endurance" },
  { key: "zone3_sec" as const, label: "Z3", color: "#00d68f", name: "Tempo" },
  { key: "zone4_sec" as const, label: "Z4", color: "#f97316", name: "Threshold" },
  { key: "zone5_sec" as const, label: "Z5", color: "#ef4444", name: "VO2max" },
];

function weekTotal(w: WeeklyHRZones): number {
  return ZONES.reduce((sum, z) => sum + w[z.key], 0);
}

function formatTime(sec: number): string {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

function formatWeekLabel(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

/** Show a label every ~N bars so they don't overlap. */
function labelInterval(count: number): number {
  if (count <= 12) return 1;
  if (count <= 26) return 2;
  return 4;
}

export function HRZoneChart({ data }: HRZoneChartProps) {
  // Aggregate totals for legend (only non-empty weeks)
  const totals = { zone1_sec: 0, zone2_sec: 0, zone3_sec: 0, zone4_sec: 0, zone5_sec: 0 };
  for (const w of data) {
    for (const z of ZONES) {
      totals[z.key] += w[z.key];
    }
  }
  const grandTotal = ZONES.reduce((sum, z) => sum + totals[z.key], 0);
  const interval = labelInterval(data.length);

  return (
    <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
      <h2 className="mb-3 text-sm font-semibold text-whoop-text">
        HR Zone Distribution
      </h2>

      {grandTotal === 0 ? (
        <div className="py-8 text-center text-xs text-whoop-text-muted">No HR zone data</div>
      ) : (
        <>
          {/* 100% stacked bars — all weeks shown */}
          <div className="flex items-stretch gap-px" style={{ height: 160 }}>
            {data.map((w, idx) => {
              const total = weekTotal(w);
              const isEmpty = total === 0;
              const showLabel = idx % interval === 0;

              return (
                <div
                  key={w.week_start}
                  className="group relative flex flex-1 flex-col"
                >
                  {/* Tooltip (only for non-empty) */}
                  {!isEmpty && (
                    <div className="pointer-events-none absolute bottom-full mb-1 left-1/2 -translate-x-1/2 hidden w-40 rounded-lg border border-whoop-border bg-whoop-card p-2 shadow-xl group-hover:block z-50">
                      <div className="text-[10px] font-semibold text-whoop-text mb-1">
                        Week of {formatWeekLabel(w.week_start)}
                      </div>
                      {ZONES.map((z) => {
                        const pct = (w[z.key] / total) * 100;
                        return w[z.key] > 0 ? (
                          <div key={z.key} className="flex items-center justify-between text-[10px]">
                            <div className="flex items-center gap-1">
                              <div className="h-1.5 w-1.5 rounded-sm" style={{ backgroundColor: z.color }} />
                              <span className="text-whoop-text-secondary">{z.label}</span>
                            </div>
                            <span className="text-whoop-text">{pct.toFixed(0)}% · {formatTime(w[z.key])}</span>
                          </div>
                        ) : null;
                      })}
                      <div className="mt-1 border-t border-whoop-border/50 pt-1 text-[10px] text-whoop-text-muted">
                        Total: {formatTime(total)}
                      </div>
                    </div>
                  )}

                  {/* Bar */}
                  {isEmpty ? (
                    <div className="flex-1 rounded-sm bg-whoop-surface/30" />
                  ) : (
                    <div className="flex flex-1 flex-col overflow-hidden rounded-sm">
                      {ZONES.slice().reverse().map((z) => {
                        const pct = (w[z.key] / total) * 100;
                        if (pct < 0.5) return null;
                        return (
                          <div
                            key={z.key}
                            style={{ height: `${pct}%`, backgroundColor: z.color }}
                          />
                        );
                      })}
                    </div>
                  )}

                  {/* Week label — always reserve space, only show text at intervals */}
                  <div className="mt-1 text-[7px] leading-none text-whoop-text-muted text-center truncate w-full">
                    {showLabel ? formatWeekLabel(w.week_start) : "\u00A0"}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Legend with overall totals */}
          <div className="mt-4 flex flex-wrap gap-x-4 gap-y-1">
            {ZONES.map((z) => {
              const pct = grandTotal > 0 ? (totals[z.key] / grandTotal) * 100 : 0;
              return (
                <div key={z.key} className="flex items-center gap-1.5 text-xs">
                  <div className="h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: z.color }} />
                  <span className="text-whoop-text-secondary">
                    {z.label} {z.name}
                  </span>
                  <span className="text-whoop-text-muted">
                    {pct.toFixed(0)}%
                  </span>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
