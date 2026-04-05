/**
 * Format a Date as YYYY-MM-DD using local timezone (not UTC).
 * Avoids the off-by-one bug from `toISOString().split("T")[0]`
 * which returns UTC and can shift the date near midnight.
 */
export function toLocalDateStr(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}
