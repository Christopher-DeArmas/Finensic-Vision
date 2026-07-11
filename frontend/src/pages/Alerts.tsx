import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Bell } from "lucide-react";
import { motion } from "framer-motion";
import { Panel } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { RISK_COLORS } from "@/components/ui/RiskBadge";
import { Select } from "@/components/ui/Select";
import { Pagination } from "@/components/ui/Pagination";
import { RowsSkeleton } from "@/components/ui/Skeleton";
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

export function Alerts() {
  const [severity, setSeverity] = useState("");
  const [status, setStatus] = useState("");
  const [rule, setRule] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<Page<AlertRead> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => setPage(1), [severity, status, rule]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    api
      .alerts({ page, page_size: 20, severity, status, rule })
      .then((d) => active && (setData(d), setLoading(false)))
      .catch(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [severity, status, rule, page]);

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
        <h1 className="text-lg font-semibold text-white">Alerts</h1>
        <p className="text-xs text-white/40">
          {data ? `${data.total} alerts` : "Loading…"}
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <Select value={severity} onChange={setSeverity} options={SEVERITY_OPTS} />
        <Select value={status} onChange={setStatus} options={STATUS_OPTS} />
        <Select value={rule} onChange={setRule} options={RULE_OPTS} />
      </div>

      <Panel title="Alert Queue" icon={<Bell size={16} />} bodyClassName="p-2">
        {loading && !data ? (
          <RowsSkeleton />
        ) : !data || data.items.length === 0 ? (
          <p className="p-6 text-center text-sm text-white/40">
            No alerts match these filters.
          </p>
        ) : (
          <>
            <ul className="divide-y divide-white/5">
              {data.items.map((a) => (
                <li
                  key={a.id}
                  className="flex items-center gap-3 rounded-lg px-3 py-2.5 transition-colors hover:bg-white/5"
                >
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
                    <span className="w-8 shrink-0 text-right text-sm font-bold tabular-nums text-white/80">
                      {a.score}
                    </span>
                  </Link>

                  {/* Status control (item 14) — outside the link so it doesn't navigate. */}
                  <select
                    value={a.status}
                    onChange={(e) => updateStatus(a.id, e.target.value)}
                    className="rounded-lg border px-2 py-1 text-xs font-medium capitalize outline-none"
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
                </li>
              ))}
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
