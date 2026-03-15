export function MiniBar({ pct, color }: { pct: number; color: string }) {
  return (
    <div className="h-1 w-full overflow-hidden rounded-sm bg-[#222]">
      <div
        className="h-full rounded-sm transition-all duration-1000 ease-out"
        style={{ width: `${Math.min(pct, 100)}%`, background: color }}
      />
    </div>
  );
}
