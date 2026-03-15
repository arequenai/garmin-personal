"use client";

import { useState } from "react";
import type { DailySection as DailySectionType } from "@/lib/types";
import { MiniBar } from "./mini-bar";
import { Ring } from "./ring";

const COLOR_MAP: Record<string, string> = {
  "whoop-green": "#00d68f",
  "whoop-teal": "#00c4b4",
  "whoop-yellow": "#f5c542",
  "whoop-red": "#ff4d4d",
  "whoop-blue": "#4da6ff",
  "whoop-purple": "#b388ff",
};

function getPctColor(p: number) {
  if (p >= 85) return "#00d68f";
  if (p >= 60) return "#f5c542";
  return "#ff4d4d";
}

export function DailySectionCard({ section }: { section: DailySectionType }) {
  const [open, setOpen] = useState(true);
  const color = COLOR_MAP[section.color] || "#888";
  const avgPct = Math.round(
    section.metrics.reduce((a, m) => a + m.pct, 0) / Math.max(section.metrics.length, 1)
  );

  return (
    <div className="overflow-hidden rounded-xl border border-whoop-border bg-whoop-card">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full cursor-pointer select-none items-center justify-between px-4 py-3.5"
      >
        <div className="flex items-center gap-2.5">
          <span className="text-lg">{section.icon}</span>
          <span
            className="text-sm font-bold uppercase tracking-widest"
            style={{ color, fontFamily: "'DM Sans', sans-serif" }}
          >
            {section.label}
          </span>
        </div>
        <div className="flex items-center gap-2.5">
          <Ring size={36} stroke={3} pct={avgPct} color={color}>
            <span
              className="text-[10px] font-extrabold text-whoop-text"
              style={{ fontFamily: "'DM Sans', sans-serif" }}
            >
              {avgPct}
            </span>
          </Ring>
          <span
            className="text-sm text-whoop-text-muted transition-transform duration-300"
            style={{ transform: open ? "rotate(180deg)" : "rotate(0)" }}
          >
            ▾
          </span>
        </div>
      </button>

      {open && (
        <div className="px-4 pb-3.5">
          {section.metrics.map((m) => (
            <div key={m.label} className="flex items-center gap-3 py-3">
              <div className="flex-1">
                <div className="mb-0.5 text-xs text-whoop-text-secondary">{m.label}</div>
                <MiniBar pct={m.pct} color={getPctColor(m.pct)} />
              </div>
              <div className="min-w-[70px] text-right">
                <span
                  className="text-lg font-extrabold text-whoop-text"
                  style={{ fontFamily: "'DM Sans', sans-serif" }}
                >
                  {m.value}
                </span>
                <span className="ml-1 text-[10px] text-whoop-text-muted">{m.unit}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
