"use client";

import type { DailySummary } from "@/lib/types";

interface BodyBatteryPatternProps {
  data: DailySummary[];
}

function formatDayLabel(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("en-US", { weekday: "short" });
}

function formatDateShort(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function BodyBatteryPattern({ data }: BodyBatteryPatternProps) {
  const chartData = [...data]
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
    .slice(-7)
    .filter((d) => d.body_battery_high != null || d.body_battery_low != null);

  if (chartData.length === 0) {
    return (
      <div className="rounded-2xl bg-bg-card p-6">
        <h2 className="font-heading text-lg font-semibold text-text-primary">
          Body Battery Pattern
        </h2>
        <div className="flex h-[250px] items-center justify-center text-text-secondary">
          No body battery data available
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl bg-bg-card p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-heading text-lg font-semibold text-text-primary">
          Body Battery Pattern
        </h2>
        <span className="text-xs text-text-secondary">Last 7 days</span>
      </div>

      <div className="flex h-[250px] items-end gap-3">
        {chartData.map((d) => {
          const high = d.body_battery_high ?? 0;
          const low = d.body_battery_low ?? 0;
          const range = high - low;

          // Scale: 0-100 maps to 0-100% of bar area height
          const barAreaHeight = 200; // px available for bars
          const bottomOffset = (low / 100) * barAreaHeight;
          const barHeight = Math.max((range / 100) * barAreaHeight, 4);

          return (
            <div
              key={d.date}
              className="group relative flex flex-1 flex-col items-center"
            >
              {/* Bar container */}
              <div
                className="relative w-full"
                style={{ height: `${barAreaHeight}px` }}
              >
                {/* Range bar */}
                <div
                  className="absolute left-1/2 w-8 -translate-x-1/2 rounded-lg transition-opacity"
                  style={{
                    bottom: `${bottomOffset}px`,
                    height: `${barHeight}px`,
                    background:
                      "linear-gradient(to top, rgba(34,197,94,0.3), rgba(34,197,94,0.7))",
                  }}
                />

                {/* High marker */}
                <div
                  className="absolute left-1/2 -translate-x-1/2 text-[10px] font-medium text-recovery"
                  style={{
                    bottom: `${bottomOffset + barHeight + 2}px`,
                  }}
                >
                  {high}
                </div>

                {/* Low marker */}
                <div
                  className="absolute left-1/2 -translate-x-1/2 text-[10px] font-medium text-text-secondary"
                  style={{
                    bottom: `${Math.max(bottomOffset - 14, 0)}px`,
                  }}
                >
                  {low}
                </div>
              </div>

              {/* Day label */}
              <div className="mt-2 text-center">
                <div className="text-xs font-medium text-text-primary">
                  {formatDayLabel(d.date)}
                </div>
                <div className="text-[10px] text-text-secondary">
                  {formatDateShort(d.date)}
                </div>
              </div>

              {/* Tooltip on hover */}
              <div className="pointer-events-none absolute -top-2 left-1/2 z-10 hidden -translate-x-1/2 rounded-lg bg-bg-primary px-3 py-1.5 text-xs shadow-lg group-hover:block">
                <span className="text-text-secondary">
                  {formatDateShort(d.date)}
                </span>
                <br />
                <span className="text-recovery">High: {high}</span>
                {" / "}
                <span className="text-text-secondary">Low: {low}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
