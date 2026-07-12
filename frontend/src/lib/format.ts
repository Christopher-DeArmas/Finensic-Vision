const usd0 = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});
const usdCompact = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  notation: "compact",
  maximumFractionDigits: 1,
});
const num = new Intl.NumberFormat("en-US");
const numCompact = new Intl.NumberFormat("en-US", {
  notation: "compact",
  maximumFractionDigits: 1,
});

export const formatCurrency = (n: number): string =>
  Math.abs(n) >= 100_000 ? usdCompact.format(n) : usd0.format(n);

export const formatNumber = (n: number): string => num.format(n);
export const formatCompact = (n: number): string => numCompact.format(n);

/**
 * Parse an API timestamp as a Date.
 *
 * The backend emits naive UTC timestamps with no timezone suffix (e.g.
 * "2026-07-11T12:00:00"). `new Date(...)` would interpret those as *local*
 * time, skewing every relative/absolute time by the viewer's UTC offset (which
 * is why recent alerts all read "0s ago"). We append "Z" when no timezone is
 * present so the value is correctly treated as UTC.
 */
export function parseApiDate(iso: string): Date {
  const hasTz = /([zZ]|[+-]\d{2}:?\d{2})$/.test(iso);
  return new Date(hasTz ? iso : `${iso}Z`);
}

/** Short relative time like "3s", "5m", "2h". */
export function relativeTime(iso: string): string {
  const then = parseApiDate(iso).getTime();
  const secs = Math.max(0, Math.round((Date.now() - then) / 1000));
  if (secs < 60) return `${secs}s ago`;
  const mins = Math.round(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.round(hrs / 24)}d ago`;
}

export function formatTime(iso: string): string {
  return parseApiDate(iso).toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}
