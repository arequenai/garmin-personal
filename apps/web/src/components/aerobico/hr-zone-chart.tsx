"use client";

import type { HRZonesData } from "@/lib/types";

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

function formatTime(sec: number): string {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

export function HRZoneChart({ data }: HRZoneChartProps) {
  const total = ZONES.reduce((sum, z) => sum + data[z.key], 0);

  return (
    <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
      <h2 className="mb-3 text-sm font-semibold text-whoop-text">
        HR Zone Distribution
        <span className="ml-2 text-xs font-normal text-whoop-text-muted">last 4 weeks</span>
      </h2>

      {total === 0 ? (
        <div className="py-8 text-center text-xs text-whoop-text-muted">No HR zone data</div>
      ) : (
        <>
          <div className="flex h-8 overflow-hidden rounded-md">
            {ZONES.map((z) => {
              const pct = (data[z.key] / total) * 100;
              if (pct < 0.5) return null;
              return (
                <div
                  key={z.key}
                  className="flex items-center justify-center text-[9px] font-bold text-white transition-all"
                  style={{ width: `${pct}%`, backgroundColor: z.color }}
                >
                  {pct >= 8 && z.label}
                </div>
              );
            })}
          </div>

          <div className="mt-3 space-y-1.5">
            {ZONES.map((z) => {
              const pct = total > 0 ? (data[z.key] / total) * 100 : 0;
              return (
                <div key={z.key} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <div className="h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: z.color }} />
                    <span className="text-whoop-text-secondary">
                      {z.label} — {z.name}
                    </span>
                  </div>
                  <span className="text-whoop-text">
                    {pct.toFixed(0)}% · {formatTime(data[z.key])}
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
