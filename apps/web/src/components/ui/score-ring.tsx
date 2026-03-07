"use client";

interface ScoreRingProps {
  score: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
}

function scoreColor(score: number): string {
  if (score >= 70) return "#22c55e";
  if (score >= 40) return "#f97316";
  return "#ef4444";
}

export function ScoreRing({
  score,
  size = 160,
  strokeWidth = 10,
  label,
}: ScoreRingProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const clampedScore = Math.max(0, Math.min(100, score));
  const offset = circumference - (clampedScore / 100) * circumference;
  const color = scoreColor(clampedScore);
  const center = size / 2;

  return (
    <div className="flex flex-col items-center">
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="-rotate-90"
      >
        {/* Background track */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="var(--color-bg-hover)"
          strokeWidth={strokeWidth}
        />
        {/* Progress arc */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-[stroke-dashoffset] duration-700 ease-out"
        />
      </svg>

      {/* Score label centered over the SVG */}
      <div
        className="flex flex-col items-center justify-center"
        style={{ marginTop: -size / 2 - size * 0.15, height: size }}
      >
        <span
          className="font-heading text-5xl font-bold tracking-tight"
          style={{ color }}
        >
          {clampedScore}
        </span>
        {label && (
          <span className="mt-1 text-sm text-text-secondary">{label}</span>
        )}
      </div>
    </div>
  );
}
