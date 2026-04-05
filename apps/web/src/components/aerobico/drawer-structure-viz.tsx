"use client";

import type { WorkoutStructure, WorkoutStructureStep } from "@/lib/types";

const INTENSITY_COLORS: Record<string, string> = {
  warmUp: "#00d68f",
  active: "#ef4444",
  coolDown: "#4da6ff",
};

function formatStepLength(step: WorkoutStructureStep): string {
  const { unit, value } = step.length;
  if (unit === "second") {
    const m = Math.floor(value / 60);
    const s = value % 60;
    return s > 0 ? `${m}:${s.toString().padStart(2, "0")}` : `${m}:00`;
  }
  if (unit === "meter") {
    return value >= 1000 ? `${(value / 1000).toFixed(1)}km` : `${value}m`;
  }
  return `${value}x`;
}

function flattenSteps(structure: WorkoutStructureStep[]): {
  label: string;
  intensityClass: string;
  widthPct: number;
  heightPct: number;
}[] {
  const blocks: { label: string; intensityClass: string; widthPct: number; heightPct: number }[] = [];

  let totalEnd = 0;
  for (const step of structure) {
    if (step.end != null && step.end > totalEnd) totalEnd = step.end;
  }
  if (totalEnd === 0) totalEnd = 1;

  for (const step of structure) {
    const begin = step.begin ?? 0;
    const end = step.end ?? totalEnd;
    const widthPct = ((end - begin) / totalEnd) * 100;

    if (step.type === "repetition" && step.steps && step.length.value > 1) {
      const reps = step.length.value;
      const subWidth = widthPct / (reps * step.steps.length);
      for (let r = 0; r < reps; r++) {
        for (const sub of step.steps) {
          const intensity = sub.intensityClass || "active";
          const maxTarget = sub.targets?.[0]?.maxValue ?? 5;
          const heightPct = Math.min((maxTarget / 10) * 100, 100);
          const name = sub.name || intensity;
          const len = formatStepLength(sub);
          blocks.push({
            label: r === 0 ? `${reps}x ${len} ${name}` : "",
            intensityClass: intensity,
            widthPct: subWidth,
            heightPct,
          });
        }
      }
    } else {
      const innerStep = step.steps?.[0] || step;
      const intensity = innerStep.intensityClass || "active";
      const maxTarget = innerStep.targets?.[0]?.maxValue ?? 5;
      const heightPct = Math.min((maxTarget / 10) * 100, 100);
      const name = innerStep.name || intensity;
      const len = formatStepLength(innerStep);
      blocks.push({
        label: `${name} ${len}`,
        intensityClass: intensity,
        widthPct,
        heightPct,
      });
    }
  }

  return blocks;
}

interface DrawerStructureVizProps {
  structure: WorkoutStructure;
}

export function DrawerStructureViz({ structure }: DrawerStructureVizProps) {
  if (!structure.structure || structure.structure.length === 0) return null;

  const blocks = flattenSteps(structure.structure);

  return (
    <div className="p-3" style={{ borderTop: "1px solid rgba(255,255,255,0.04)" }}>
      <div className="mb-2 text-[10px] font-semibold text-whoop-text-muted">Workout Structure</div>
      <div className="flex items-end gap-px" style={{ height: "60px" }}>
        {blocks.map((block, i) => (
          <div
            key={i}
            className="relative flex flex-col items-center justify-end"
            style={{ width: `${block.widthPct}%`, height: "100%" }}
          >
            {block.label && (
              <div className="absolute -top-3.5 left-0 truncate text-[8px] text-whoop-text-muted whitespace-nowrap">
                {block.label}
              </div>
            )}
            <div
              className="w-full rounded-t-sm"
              style={{
                height: `${block.heightPct}%`,
                backgroundColor: INTENSITY_COLORS[block.intensityClass] || "#6b7280",
                opacity: block.intensityClass === "active" ? 0.85 : 0.6,
              }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
