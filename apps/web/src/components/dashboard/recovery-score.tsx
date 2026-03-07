import { ScoreRing } from "@/components/ui/score-ring";
import type { PerformanceMetric, SleepSession } from "@/lib/types";

interface RecoveryScoreProps {
  performance: PerformanceMetric | null;
  sleep: SleepSession | null;
}

function recoveryLabel(score: number): string {
  if (score >= 70) return "Great";
  if (score >= 40) return "Moderate";
  return "Low";
}

export function RecoveryScore({ performance, sleep }: RecoveryScoreProps) {
  const score = performance?.recovery_score
    ? Math.round(performance.recovery_score)
    : null;

  const hrvText =
    sleep?.avg_hrv != null ? `HRV ${Math.round(sleep.avg_hrv)}ms` : null;
  const sleepText =
    sleep?.sleep_score != null ? `Sleep ${sleep.sleep_score}` : null;
  const tsbText =
    performance?.tsb != null
      ? `TSB ${performance.tsb >= 0 ? "+" : ""}${Math.round(performance.tsb)}`
      : null;

  const factors = [hrvText, sleepText, tsbText].filter(Boolean).join(" \u00B7 ");

  return (
    <div className="flex flex-col items-center justify-center rounded-2xl bg-bg-card p-8">
      <span className="mb-4 text-sm font-medium tracking-wide text-text-secondary uppercase">
        Recovery
      </span>

      {score != null ? (
        <>
          <ScoreRing score={score} size={180} strokeWidth={12} />
          <p className="mt-2 text-lg font-semibold text-text-primary">
            {recoveryLabel(score)}
          </p>
          {factors && (
            <p className="mt-1.5 text-xs text-text-secondary">{factors}</p>
          )}
        </>
      ) : (
        <div className="flex h-[180px] items-center justify-center">
          <span className="text-text-secondary">&mdash;</span>
        </div>
      )}
    </div>
  );
}
