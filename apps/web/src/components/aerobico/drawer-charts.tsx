"use client";

import type { CompletedWorkoutDetail } from "@/lib/types";

const HR_ZONE_COLORS = ["#00d68f", "#4da6ff", "#f59e0b", "#ef4444", "#dc2626"];
const HR_ZONE_LABELS = ["Z1", "Z2", "Z3", "Z4", "Z5"];

function formatZoneTime(sec: number): string {
  if (sec < 60) return `${sec}s`;
  const m = Math.floor(sec / 60);
  return `${m}m`;
}

function speedToPace(mps: number): string {
  if (mps <= 0) return "—";
  const secPerKm = 1000 / mps;
  const min = Math.floor(secPerKm / 60);
  const sec = Math.round(secPerKm % 60);
  return `${min}:${sec.toString().padStart(2, "0")}`;
}

const PACE_DISTANCE_LABELS: Record<string, string> = {
  MM400Meter: "400m",
  MM800Meter: "800m",
  MM1Kilometer: "1 km",
  MM1Mile: "1 mi",
  MM5Kilometer: "5 km",
  MM10Kilometer: "10 km",
  MMHalfMarathon: "HM",
  MMMarathon: "Marathon",
};

const PACE_DISTANCE_ORDER = [
  "MM400Meter", "MM800Meter", "MM1Kilometer", "MM5Kilometer", "MM10Kilometer",
];

interface DrawerChartsProps {
  workout: CompletedWorkoutDetail;
}

export function DrawerCharts({ workout }: DrawerChartsProps) {
  const details = workout.workout_details_json;
  if (!details) return null;

  const hrZones = details.timeInHeartRateZones?.timeInZones || [];
  const speedZones = details.timeInSpeedZones?.timeInZones || [];
  const bestPaces = details.meanMaxSpeedsByDistance?.meanMaxes || [];

  const hasHR = hrZones.length > 0 && hrZones.some((z) => z.seconds > 0);
  const hasSpeed = speedZones.length > 0 && speedZones.some((z) => z.seconds > 0);
  const hasBestPaces = bestPaces.some((p) => p.value != null && p.value > 0);

  if (!hasHR && !hasSpeed && !hasBestPaces) return null;

  const maxHRSec = Math.max(...hrZones.map((z) => z.seconds), 1);
  const maxSpeedSec = Math.max(...speedZones.map((z) => z.seconds), 1);

  return (
    <div className="flex" style={{ borderTop: "1px solid rgba(255,255,255,0.04)" }}>
      {hasHR && (
        <div className="flex-1 p-3" style={{ borderRight: hasSpeed || hasBestPaces ? "1px solid rgba(255,255,255,0.04)" : undefined }}>
          <div className="mb-2 text-[10px] font-semibold text-whoop-text-muted">HR Zones</div>
          <div className="flex items-end gap-1" style={{ height: "60px" }}>
            {hrZones.slice(0, 5).map((z, i) => (
              <div key={i} className="flex flex-1 flex-col items-center gap-0.5">
                <div className="text-[9px] text-whoop-text-muted">
                  {z.seconds > 0 ? formatZoneTime(z.seconds) : ""}
                </div>
                <div
                  className="w-full rounded-t"
                  style={{
                    height: `${Math.max((z.seconds / maxHRSec) * 48, 2)}px`,
                    backgroundColor: HR_ZONE_COLORS[i] || "#6b7280",
                  }}
                />
                <div className="text-[9px] text-whoop-text-muted">{HR_ZONE_LABELS[i]}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {hasSpeed && (
        <div className="flex-1 p-3" style={{ borderRight: hasBestPaces ? "1px solid rgba(255,255,255,0.04)" : undefined }}>
          <div className="mb-2 text-[10px] font-semibold text-whoop-text-muted">Pace Zones</div>
          <div className="flex items-end gap-1" style={{ height: "60px" }}>
            {speedZones.slice(0, 5).map((z, i) => (
              <div key={i} className="flex flex-1 flex-col items-center gap-0.5">
                <div className="text-[9px] text-whoop-text-muted">
                  {z.seconds > 0 ? formatZoneTime(z.seconds) : ""}
                </div>
                <div
                  className="w-full rounded-t"
                  style={{
                    height: `${Math.max((z.seconds / maxSpeedSec) * 48, 2)}px`,
                    backgroundColor: "#a855f7",
                    opacity: 0.5 + (i / 5) * 0.5,
                  }}
                />
                <div className="truncate text-[8px] text-whoop-text-muted" title={z.label}>
                  {z.label.replace(/ Run$/, "").slice(0, 4)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {hasBestPaces && (
        <div className="flex-1 p-3">
          <div className="mb-2 text-[10px] font-semibold text-whoop-text-muted">Best Paces</div>
          <div className="space-y-1">
            {PACE_DISTANCE_ORDER.map((key) => {
              const entry = bestPaces.find((p) => p.label === key);
              if (!entry || entry.value == null || entry.value <= 0) return null;
              return (
                <div key={key} className="flex justify-between text-[11px]">
                  <span className="text-whoop-text-muted">{PACE_DISTANCE_LABELS[key] || key}</span>
                  <span className="text-whoop-text">{speedToPace(entry.value)} /km</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
