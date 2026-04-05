import type { SyncSourceStatus } from "@/lib/types";

function daysAgoLabel(lastDate: string | null, today: string): string {
  if (!lastDate) return "never";
  if (lastDate === today) return "today";
  const diff = Math.round(
    (new Date(today).getTime() - new Date(lastDate).getTime()) / 86_400_000,
  );
  return `${diff}d ago`;
}

export function SyncStatusBar({
  status,
  today,
}: {
  status: SyncSourceStatus[];
  today: string;
}) {
  const stale = status.filter((s) => !s.ok);
  if (stale.length === 0) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 border-t border-yellow-800/40 bg-yellow-950/90 px-4 py-2 text-xs text-yellow-300 backdrop-blur-sm">
      <div className="mx-auto flex max-w-[1200px] items-center gap-3">
        <span className="shrink-0 font-medium">Sync issues:</span>
        <div className="flex flex-wrap gap-x-4 gap-y-1">
          {stale.map((s) => (
            <span key={s.source} className="flex items-center gap-1.5">
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-yellow-400" />
              {s.source}
              <span className="text-yellow-500">
                {daysAgoLabel(s.last_date, today)}
              </span>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
