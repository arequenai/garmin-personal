"use client";

import { useState } from "react";
import type { OverviewData } from "@/lib/types";
import { CategoryCard } from "./category-card";
import { DailySectionCard } from "./daily-section";
import { Ring } from "./ring";

const CATEGORY_CONFIG = [
  { id: "running", label: "Running", icon: "\u{1F3C3}", color: "#00d68f" },
  { id: "strength", label: "Strength", icon: "\u{1F4AA}", color: "#00c4b4" },
  { id: "recovery", label: "Recovery", icon: "\u{1F50B}", color: "#f5c542" },
  { id: "sleep", label: "Sleep", icon: "\u{1F634}", color: "#ff4d4d" },
  { id: "body", label: "Body Comp", icon: "\u2696\uFE0F", color: "#b388ff" },
  { id: "glucose", label: "Glucose", icon: "\u{1FA78}", color: "#4da6ff" },
] as const;

const COLOR_MAP: Record<string, string> = {
  "whoop-green": "#00d68f",
  "whoop-teal": "#00c4b4",
  "whoop-yellow": "#f5c542",
  "whoop-red": "#ff4d4d",
  "whoop-blue": "#4da6ff",
  "whoop-purple": "#b388ff",
};

export function OverviewClient({ data }: { data: OverviewData }) {
  const [view, setView] = useState<"full" | "daily">("full");

  const today = new Date();
  const dateStr = today.toLocaleDateString("en-US", {
    weekday: "long",
    month: "short",
    day: "numeric",
  });

  return (
    <div
      className="min-h-screen bg-whoop-bg text-whoop-text"
      style={{ fontFamily: "'DM Sans', sans-serif" }}
    >
      {/* Top bar */}
      <div className="sticky top-0 z-50 flex items-center justify-between border-b border-whoop-border bg-whoop-bg/90 px-6 py-3 backdrop-blur-xl">
        <div>
          <div className="text-lg font-extrabold tracking-tight">
            <span className="text-whoop-green">O</span>VERVIEW
          </div>
          <div className="text-[11px] tracking-wider text-whoop-text-muted">
            {dateStr.toUpperCase()}
          </div>
        </div>

        <div className="flex gap-0.5 rounded-xl bg-whoop-surface p-1">
          {(["full", "daily"] as const).map((v) => (
            <button
              key={v}
              onClick={() => setView(v)}
              className="rounded-lg border-none px-4 py-1.5 text-[11px] font-bold uppercase tracking-widest transition-all duration-300"
              style={{
                background: view === v ? "#00d68f" : "transparent",
                color: view === v ? "#000" : "#555",
                fontFamily: "'DM Sans', sans-serif",
                cursor: "pointer",
              }}
            >
              {v}
            </button>
          ))}
        </div>
      </div>

      {/* Full view */}
      {view === "full" && (
        <div className="mx-auto max-w-[1200px] px-6 py-6 pb-16">
          <div className="grid grid-cols-3 gap-5">
            {CATEGORY_CONFIG.map((cfg) => {
              const cat = data.categories[cfg.id];
              if (!cat) return null;
              return (
                <CategoryCard
                  key={cfg.id}
                  category={cat}
                  label={cfg.label}
                  icon={cfg.icon}
                  color={cfg.color}
                />
              );
            })}
          </div>
        </div>
      )}

      {/* Daily view */}
      {view === "daily" && (
        <div className="mx-auto max-w-[480px] px-4 py-5 pb-20">
          <div className="mb-6 text-center">
            <div className="mb-2 text-[11px] uppercase tracking-widest text-whoop-text-muted">
              Today&apos;s Snapshot
            </div>
            <div className="flex justify-center gap-3">
              {data.daily_sections.map((s) => {
                const avg = Math.round(
                  s.metrics.reduce((a, m) => a + m.pct, 0) / Math.max(s.metrics.length, 1)
                );
                const color = COLOR_MAP[s.color] || "#888";
                return (
                  <Ring key={s.id} size={44} stroke={3.5} pct={avg} color={color}>
                    <span className="text-[11px] font-extrabold text-whoop-text">{avg}</span>
                  </Ring>
                );
              })}
            </div>
          </div>

          <div className="flex flex-col gap-3">
            {data.daily_sections.map((section) => (
              <DailySectionCard key={section.id} section={section} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
