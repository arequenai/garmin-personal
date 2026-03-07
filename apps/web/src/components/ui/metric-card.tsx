import type { ReactNode } from "react";
import { ArrowDown, ArrowUp } from "lucide-react";

interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  trend?: {
    value: number;
    direction: "up" | "down";
  };
  icon?: ReactNode;
  accentColor?: string;
}

export function MetricCard({
  label,
  value,
  unit,
  trend,
  icon,
  accentColor = "text-text-primary",
}: MetricCardProps) {
  const trendIsPositive = trend?.direction === "up";
  const TrendIcon = trendIsPositive ? ArrowUp : ArrowDown;

  return (
    <div className="rounded-2xl bg-bg-card p-6">
      <div className="flex items-center gap-2">
        {icon && <span className={`${accentColor} opacity-70`}>{icon}</span>}
        <span className="text-sm text-text-secondary">{label}</span>
      </div>

      <div className="mt-3 flex items-baseline gap-1.5">
        <span
          className={`font-heading text-4xl font-bold tracking-tight ${accentColor}`}
        >
          {value}
        </span>
        {unit && (
          <span className="text-sm font-medium text-text-secondary">
            {unit}
          </span>
        )}
      </div>

      {trend && (
        <div className="mt-2 flex items-center gap-1">
          <TrendIcon
            size={14}
            className={trendIsPositive ? "text-recovery" : "text-alert"}
          />
          <span
            className={`text-xs font-medium ${
              trendIsPositive ? "text-recovery" : "text-alert"
            }`}
          >
            {trendIsPositive ? "+" : ""}
            {trend.value}%
          </span>
        </div>
      )}
    </div>
  );
}
