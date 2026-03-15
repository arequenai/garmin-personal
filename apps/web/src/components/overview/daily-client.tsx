"use client";

import type { OverviewData } from "@/lib/types";

interface PanelConfig {
  id: string;
  label: string;
  color: string;
  metrics: string[];
}

const PANELS: PanelConfig[] = [
  { id: "nutrition", label: "Nutrition", color: "#00d68f", metrics: ["Net Cal", "Weight", "Protein"] },
  { id: "recovery", label: "Recovery", color: "#f5c542", metrics: ["Recovery", "Battery", "Stress"] },
  { id: "sleep", label: "Sleep", color: "#ff4d4d", metrics: ["Sleep Quality", "Time in Bed", "Bed Behavior"] },
  { id: "running", label: "Running", color: "#4da6ff", metrics: ["Training Readiness", "km L7D", "m+ L7D"] },
  { id: "strength", label: "Strength", color: "#00c4b4", metrics: ["Days since Jefit", "Pull-ups Max", "Strength Time"] },
  { id: "glucose", label: "Glucose", color: "#b388ff", metrics: ["Recent Glucose", "Fasting Glucose", "Mean Glucose"] },
];

export function DailyClient({ data }: { data: OverviewData }) {
  // Build a flat lookup: "label" → { value, unit }
  const lookup = new Map<string, { value: string; unit: string }>();
  for (const section of data.daily_sections) {
    for (const m of section.metrics) {
      lookup.set(m.label, { value: String(m.value), unit: m.unit });
    }
  }

  const today = new Date();
  const dateStr = today.toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
  });

  return (
    <div
      className="flex-1 bg-whoop-bg text-whoop-text"
      style={{ fontFamily: "'DM Sans', sans-serif" }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 md:px-6 md:py-3">
        <div className="text-sm font-extrabold tracking-tight md:text-lg">
          <span className="text-whoop-green">D</span>AILY
        </div>
        <div className="text-[10px] tracking-wider text-whoop-text-muted md:text-xs">
          {dateStr.toUpperCase()}
        </div>
      </div>

      {/* Panel grid — 2 cols on mobile, 3 cols on desktop */}
      <div className="mx-auto max-w-4xl px-3 pb-4 md:px-6">
        <div className="grid grid-cols-2 gap-2 md:grid-cols-3 md:gap-3">
          {PANELS.map((panel) => (
            <div
              key={panel.id}
              className="rounded-lg border border-whoop-border bg-whoop-card px-3 py-2 md:px-4 md:py-3"
            >
              <div
                className="mb-2 text-[11px] font-bold uppercase tracking-widest md:text-xs"
                style={{ color: panel.color }}
              >
                {panel.label}
              </div>
              <div className="flex flex-col gap-1.5">
                {panel.metrics.map((label) => {
                  const found = lookup.get(label);
                  const value = found?.value ?? "--";
                  const unit = found?.unit ?? "";
                  return (
                    <div key={label} className="flex items-baseline justify-between">
                      <span className="text-[10px] text-whoop-text-secondary md:text-xs">
                        {label}
                        {unit && (
                          <span className="ml-0.5 text-whoop-text-muted">({unit})</span>
                        )}
                      </span>
                      <span className="text-xs font-bold text-whoop-text md:text-sm">
                        {value}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
