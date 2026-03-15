"use client";

import type { OverviewData } from "@/lib/types";
import { CategoryCard } from "./category-card";

const CATEGORY_CONFIG = [
  { id: "running", label: "Running", icon: "\u{1F3C3}", color: "#00d68f" },
  { id: "strength", label: "Strength", icon: "\u{1F4AA}", color: "#00c4b4" },
  { id: "recovery", label: "Recovery", icon: "\u{1F50B}", color: "#f5c542" },
  { id: "sleep", label: "Sleep", icon: "\u{1F634}", color: "#ff4d4d" },
  { id: "body", label: "Body Comp", icon: "\u2696\uFE0F", color: "#b388ff" },
  { id: "glucose", label: "Glucose", icon: "\u{1FA78}", color: "#4da6ff" },
] as const;

export function OverviewClient({ data }: { data: OverviewData }) {
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
      </div>

      {/* Full view */}
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
    </div>
  );
}
