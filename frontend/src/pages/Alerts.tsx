import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ChevronDown, ListFilter } from "lucide-react";
import { motion } from "framer-motion";
import { Panel } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { RISK_COLORS } from "@/components/ui/RiskBadge";
import { Select } from "@/components/ui/Select";
import { Pagination } from "@/components/ui/Pagination";
import { RowsSkeleton } from "@/components/ui/Skeleton";
import { cn } from "@/lib/cn";
import { relativeTime } from "@/lib/format";
import { api } from "@/services/api";
import type { AlertRead, Page, Severity } from "@/types/api";

const SEVERITY_OPTS = [
  { value: "", label: "All severities" },
  { value: "critical", label: "Critical" },
  { value: "high", label: "High" },
  { value: "medium", label: "Medium" },
  { value: "low", label: "Low" },
];
const STATUS_OPTS = [
  { value: "", label: "All statuses" },
  { value: "open", label: "Open" },
  { value: "in_review", label: "In review" },
  { value: "escalated", label: "Escalated" },
  { value: "dismissed", label: "Dismissed" },
];
const RULE_OPTS = [
  { value: "", label: "All rules" },
  { value: "AML-01", label: "AML-01 Structuring" },
  { value: "AML-02", label: "AML-02 Rapid Movement" },
  { value: "AML-03", label: "AML-03 Circular Transfers" },
  { value: "AML-04", label: "AML-04 Dormant Awakening" },
  { value: "AML-05", label: "AML-05 Velocity" },
  { value: "AML-06", label: "AML-06 Geo Anomaly" },
  { value: "AML-07", label: "AML-07 Multiple Sources" },
  { value: "AML-08", label: "AML-08 High-Risk Jurisdiction" },
  { value: "AML-09", label: "AML-09 Large Cash" },
  { value: "AML-10", label: "AML-10 Account Explosion" },
];
const SORT_OPTS = [
  { value: "triage", label: "Triage priority" },
  { value: "recent", label: "Most recent" },
];
const ROW_STATUS = [
  { value: "open", label: "Open" },
  { value: "in_review", label: "In review" },
  { value: "escalated", label: "Escalated" },
  { value: "dismissed", label: "Dismissed" },
];
const STATUS_COLOR: Record<string, string> = {
  open: "#eab308",
  in_review: "#4d9bff",
  escalated: "#f97316",
  dismissed: "#8a8a92",
};

const FACTOR_META: Record<string, { label: string; desc: string }> = {
  base_score: {
    label: "Rule score",
    desc: "55% of the alert's underlying rule score (0–100). This is the combined risk from every detection rule that fired, forming the backbone of the priority.",
  },
  severity: {
    label: "Severity",
    desc: "Bonus for the alert's highest severity band — Critical +18, High +10, Medium +4, Low +0 — so the most serious alerts float to the top.",
  },
  corroboration: {
    label: "Corroboration",
    desc: "Confidence bonus when several independent rules flag the same customer: +4 per additional rule, capped at +12. More agreeing rules means fewer false positives.",
  },
  recency: {
    label: "Recency",
    desc: "Freshness boost of up to +8 that decays over ~48 hours, keeping newly detected activity near the top of the queue.",
  },
  status: {
    label: "Disposition",
    desc: "Adjustment for the analyst's current call — Open +6, Escalated +5, In review +3, Dismissed −40 — which pushes confirmed false positives down and out of the way.",
  },
};

function triageColor(score: number): string {
  if (score >= 75) return "#ef4444";
  if (score >= 55) return "#f97316";
  if (score >= 40) return "#eab308";
  return "#4d9bff";
}

/** Triage factor pill with a hover/click popover explaining the component. */
function FactorChip({ name, value }: { name: string; value: number }) {
  const [open, setOpen] = useState(false);
  const meta = FACTOR_META[name];
  const label = meta?.label ?? name;
  return (
    <span className="group relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        onMouseLeave={() => setOpen(false)}
        className="flex items-center gap-1.5 rounded-md border border-white/5 bg-ink-900/50 px-2 py-1 text-[11px] transition-colors hover:border-white/20"
      >
        <span className="text-white/40">{label}</span>
        <span
          className={cn(
            "font-semibold tabular-nums",
            value < 0 ? "text-risk-medium" : "text-white/75",
          )}
        >
          {value > 0 ? "+" : ""}
          {value}
        </span>
      </button>
      {meta && (
        <span
          className={cn(
            "pointer-events-none absolute bottom-full left-0 z-30 mb-1.5 w-60 rounded-lg border border-white/10 bg-ink-900/95 p-2.5 text-[11px] leading-relaxed text-white/70 shadow-card backdrop-blur transition-opacity duration-150 group-hover:opacity-100",
            open ? "opacity-100" : "opacity-0",
          )}
        >
          <span className="mb-0.5 block font-semibold text-white/90">{label}</span>
          {meta.desc}
        </span>
      )}
    </span>
  );
}

export function Alerts() {
  const [severity, setSeverity] = useState("");
  const [status, setStatus] = useState("");
  const [rule, setRule] = useState("");
  const [sort, setSort] = useState("triage");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<Page<AlertRead> | null>(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<number | null>(null);

  useEffect(() => setPage(1), [severity, status, rule, sort]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    api
      .alerts({ page, page_size: 20, severity, status, rule, sort })
      .then((d) => active && (setData(d), setLoading(false)))
      .catch(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [severity, status, rule, sort, page]);

  const updateStatus = (id: number, next: string) => {
    setData((d) =>
      d
        ? { ...d, items: d.items.map((a) => (a.id === id ? { ...a, status: next } : a)) }
        : d,
    );
    api.updateAlert(id, next).catch(() => {});
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="space-y-4"
    >
      <div>
        <h1 className="text-lg font-semibold text-white">Triage Queue</h1>
        <p className="text-xs text-white/40">
          {data ? `${data.total} alerts` : "Loading…"} · ranked by composite risk
          priority
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <Select value={sort} onChange={setSort} options={SORT_OPTS} />
        <Select value={severity} onChange={setSeverity} options={SEVERITY_OPTS} />
        <Select value={status} onChange={setStatus} options={STATUS_OPTS} />
        <Select value={rule} onChange={setRule} options={RULE_OPTS} />
      </div>

      <Panel title="Prioritized Alerts" icon={<ListFilter size={16} />} bodyClassName="p-2">
        {loading && !data ? (
          <RowsSkeleton />
        ) : !data || data.items.length === 0 ? (
          <p className="p-6 text-center text-sm text-white/40">
            No alerts match these filters.
          </p>
        ) : (
          <>
            <ul className="divide-y divide-white/5">
              {data.items.map((a) => {
                const tc = triageColor(a.triage_score);
                const isOpen = expanded === a.id;
                return (
                  <li key={a.id} className="rounded-lg px-2 py-1">
                    <div className="flex items-center gap-3 py-1.5">
                      {/* Rank */}
                      <div
                        className="flex w-9 shrink-0 flex-col items-center justify-center rounded-md border py-1"
                        style={{ borderColor: `${tc}44`, backgroundColor: `${tc}12` }}
                        title={`Triage rank #${a.rank}`}
                      >
                        <span className="text-[9px] font-medium uppercase text-white/35">
                          rank
                        </span>
                        <span
                          className="text-sm font-bold leading-none tabular-nums"
                          style={{ color: tc }}
                        >
                          {a.rank || "—"}
                        </span>
                      </div>

                      <Link
                        to={`/investigations/${a.customer_id}`}
                        className="flex min-w-0 flex-1 items-center gap-3"
                      >
                        <span
                          className="h-2.5 w-2.5 shrink-0 rounded-full"
                          style={{ backgroundColor: RISK_COLORS[a.severity as Severity] }}
                        />
                        <div className="min-w-0 flex-1">
                          <div className="truncate text-sm font-medium text-white/90">
                            {a.title}
                          </div>
                          <div className="mt-1 flex flex-wrap items-center gap-1.5">
                            {a.triggered_rules.slice(0, 4).map((r) => (
                              <Badge
                                key={r}
                                className="border-white/10 bg-white/5 text-white/50"
                              >
                                {r}
                              </Badge>
                            ))}
                            <span className="text-[11px] text-white/30">
                              {relativeTime(a.created_at)}
                            </span>
                          </div>
                        </div>
                      </Link>

                      {/* Triage score bar */}
                      <div className="hidden w-32 shrink-0 sm:block">
                        <div className="mb-1 flex items-center justify-between">
                          <span className="text-[10px] uppercase text-white/35">
                            Priority
                          </span>
                          <span
                            className="text-xs font-bold tabular-nums"
                            style={{ color: tc }}
                          >
                            {a.triage_score.toFixed(0)}
                          </span>
                        </div>
                        <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/10">
                          <div
                            className="h-full rounded-full"
                            style={{
                              width: `${Math.min(100, a.triage_score)}%`,
                              backgroundColor: tc,
                            }}
                          />
                        </div>
                      </div>

                      {/* Why this rank */}
                      <button
                        onClick={() => setExpanded(isOpen ? null : a.id)}
                        className="hidden shrink-0 items-center gap-1 rounded-md border border-white/10 px-2 py-1 text-[11px] text-white/50 transition-colors hover:bg-white/5 md:flex"
                      >
                        Why
                        <ChevronDown
                          size={12}
                          className={cn("transition-transform", isOpen && "rotate-180")}
                        />
                      </button>

                      {/* Status control */}
                      <select
                        value={a.status}
                        onChange={(e) => updateStatus(a.id, e.target.value)}
                        className="shrink-0 rounded-lg border px-2 py-1 text-xs font-medium capitalize outline-none"
                        style={{
                          borderColor: `${STATUS_COLOR[a.status] ?? "#8a8a92"}55`,
                          backgroundColor: `${STATUS_COLOR[a.status] ?? "#8a8a92"}1a`,
                          color: STATUS_COLOR[a.status] ?? "#8a8a92",
                        }}
                      >
                        {ROW_STATUS.map((o) => (
                          <option key={o.value} value={o.value} className="bg-ink-850 text-white">
                            {o.label}
                          </option>
                        ))}
                      </select>
                    </div>

                    {isOpen && (
                      <div className="mb-1 ml-12 flex flex-wrap items-center gap-2 pb-1.5">
                        <span className="text-[11px] text-white/30">
                          Priority ={" "}
                        </span>
                        {Object.entries(a.triage_factors ?? {}).map(([k, v]) => (
                          <FactorChip key={k} name={k} value={v} />
                        ))}
                        <span className="text-[11px] text-white/30">
                          = {a.triage_score.toFixed(0)} · hover a factor to learn more
                        </span>
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
            <Pagination
              page={data.page}
              pages={data.pages}
              total={data.total}
              onPage={setPage}
            />
          </>
        )}
      </Panel>
    </motion.div>
  );
}
