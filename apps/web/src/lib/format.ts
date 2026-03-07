/**
 * Format a duration in minutes to "Xh Ym" style.
 */
export function formatDurationMin(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (h === 0) return `${m}m`;
  return `${h}h ${m}m`;
}

/**
 * Format a duration in seconds to "H:MM:SS" style.
 */
export function formatDurationSec(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  const mm = String(m).padStart(2, "0");
  const ss = String(s).padStart(2, "0");
  if (h > 0) return `${h}:${mm}:${ss}`;
  return `${m}:${ss}`;
}

/**
 * Format meters to kilometers with one decimal.
 */
export function formatDistanceKm(meters: number): string {
  return (meters / 1000).toFixed(1);
}

/**
 * Format a number with comma separators (e.g. 10234 -> "10,234").
 */
export function formatNumber(n: number): string {
  return n.toLocaleString("en-US");
}
