"use client";

interface GaugeProps {
  value: number;
  max?: number;
  label?: string;
  showValue?: boolean;
}

export function Gauge({
  value,
  max = 100,
  label,
  showValue = true,
}: GaugeProps) {
  const clamped = Math.max(0, Math.min(value, max));
  const pct = (clamped / max) * 100;

  return (
    <div className="flex flex-col gap-2">
      {(label || showValue) && (
        <div className="flex items-baseline justify-between">
          {label && (
            <span className="text-sm text-text-secondary">{label}</span>
          )}
          {showValue && (
            <span className="font-heading text-lg font-bold tracking-tight text-text-primary">
              {clamped}
              <span className="text-xs font-normal text-text-secondary">
                /{max}
              </span>
            </span>
          )}
        </div>
      )}

      <div className="h-2 w-full overflow-hidden rounded-full bg-bg-hover">
        <div
          className="h-full rounded-full transition-[width] duration-700 ease-out"
          style={{
            width: `${pct}%`,
            background:
              "linear-gradient(90deg, #ef4444 0%, #f97316 40%, #22c55e 100%)",
          }}
        />
      </div>
    </div>
  );
}
