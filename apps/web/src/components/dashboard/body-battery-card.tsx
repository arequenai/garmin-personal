import { Gauge } from "@/components/ui/gauge";
import type { DailySummary } from "@/lib/types";

interface BodyBatteryCardProps {
  daily: DailySummary | null;
}

export function BodyBatteryCard({ daily }: BodyBatteryCardProps) {
  const high = daily?.body_battery_high;
  const low = daily?.body_battery_low;

  return (
    <div className="flex flex-col items-center justify-center rounded-2xl bg-bg-card p-8">
      <span className="mb-4 text-sm font-medium tracking-wide text-text-secondary uppercase">
        Body Battery
      </span>

      {high != null ? (
        <div className="flex w-full flex-col items-center gap-5">
          <div className="w-full max-w-[240px]">
            <Gauge value={high} max={100} showValue />
          </div>
          <p className="text-sm text-text-secondary">
            High: <span className="font-medium text-text-primary">{high}</span>
            {low != null && (
              <>
                {" \u00B7 "}
                Low:{" "}
                <span className="font-medium text-text-primary">{low}</span>
              </>
            )}
          </p>
        </div>
      ) : (
        <div className="flex h-[100px] items-center justify-center">
          <span className="text-text-secondary">&mdash;</span>
        </div>
      )}
    </div>
  );
}
