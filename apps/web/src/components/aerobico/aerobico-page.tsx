"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { useAerobicPMC } from "@/lib/hooks/use-aerobic-pmc";
import { useAerobicVolume } from "@/lib/hooks/use-aerobic-volume";
import { useAerobicHRZones } from "@/lib/hooks/use-aerobic-hr-zones";
import { PMCChart } from "./pmc-chart";
import { TrainingCalendar } from "./training-calendar";
import { HRZoneChart } from "./hr-zone-chart";
import { WeeklyVolumeChart } from "./weekly-volume-chart";

function defaultFrom(monthsBack: number): string {
  const d = new Date();
  d.setMonth(d.getMonth() - monthsBack);
  return d.toISOString().split("T")[0];
}

function today(): string {
  return new Date().toISOString().split("T")[0];
}

const PRESETS = [
  { label: "3M", months: 3 },
  { label: "6M", months: 6 },
  { label: "1Y", months: 12 },
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

export function AerobicoPageClient() {
  const [from, setFrom] = useState(() => defaultFrom(12));
  const [to, setTo] = useState(today);
  const [activePreset, setActivePreset] = useState("1Y");

  const pmc = useAerobicPMC(from, to);
  const volume = useAerobicVolume(from, to);
  const hrZones = useAerobicHRZones(from, to);

  const applyPreset = (months: number, label: string) => {
    setFrom(defaultFrom(months));
    setTo(today());
    setActivePreset(label);
  };

  const retryPmc = () => { setFrom((f) => f); };
  const retryVolume = () => { setFrom((f) => f); };
  const retryHrZones = () => { setFrom((f) => f); };

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
                onClick={() => applyPreset(p.months, p.label)}
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
              onChange={(e) => { setFrom(e.target.value); setActivePreset(""); }}
              className="rounded-md border border-whoop-border bg-whoop-surface px-2 py-1 text-xs text-whoop-text"
            />
            <input
              type="date"
              value={to}
              onChange={(e) => { setTo(e.target.value); setActivePreset(""); }}
              className="rounded-md border border-whoop-border bg-whoop-surface px-2 py-1 text-xs text-whoop-text"
            />
          </div>
        </div>

        {/* PMC Chart */}
        {pmc.loading && (
          <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
            <div className="h-[350px] animate-pulse rounded bg-whoop-surface" />
          </div>
        )}
        {pmc.error && (
          <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
            <ChartError onRetry={retryPmc} />
          </div>
        )}
        {pmc.data && <PMCChart data={pmc.data} />}

        {/* Calendar + HR Zones row */}
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <TrainingCalendar />

          <div>
            {hrZones.loading && (
              <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
                <div className="h-[200px] animate-pulse rounded bg-whoop-surface" />
              </div>
            )}
            {hrZones.error && (
              <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
                <ChartError onRetry={retryHrZones} />
              </div>
            )}
            {hrZones.data && <HRZoneChart data={hrZones.data} />}
          </div>
        </div>

        {/* Weekly Volume */}
        <div className="mt-4">
          {volume.loading && (
            <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
              <div className="h-[250px] animate-pulse rounded bg-whoop-surface" />
            </div>
          )}
          {volume.error && (
            <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
              <ChartError onRetry={retryVolume} />
            </div>
          )}
          {volume.data && <WeeklyVolumeChart data={volume.data} />}
        </div>
      </div>
    </div>
  );
}
