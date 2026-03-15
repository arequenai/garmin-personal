const COLORS = {
  green: "#00d68f",
  greenDim: "rgba(0,214,143,0.15)",
  red: "#ff4d4d",
  redDim: "rgba(255,77,77,0.12)",
  muted: "#555555",
};

export function TrendBadge({
  value,
  invert = false,
}: {
  value: number;
  invert?: boolean;
}) {
  const positive = invert ? value < 0 : value > 0;
  const color = positive ? COLORS.green : value === 0 ? COLORS.muted : COLORS.red;
  const bg = positive ? COLORS.greenDim : value === 0 ? "transparent" : COLORS.redDim;
  const arrow = value > 0 ? "\u2191" : value < 0 ? "\u2193" : "\u2192";

  return (
    <span
      className="inline-block rounded text-[11px] font-semibold"
      style={{ color, background: bg, padding: "2px 6px", letterSpacing: 0.3 }}
    >
      {arrow} {Math.abs(value)}%
    </span>
  );
}
