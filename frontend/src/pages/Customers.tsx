import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ChevronRight, Search, Users } from "lucide-react";
import { motion } from "framer-motion";
import { Panel } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { RiskBadge, RISK_COLORS } from "@/components/ui/RiskBadge";
import { Select } from "@/components/ui/Select";
import { Pagination } from "@/components/ui/Pagination";
import { RowsSkeleton } from "@/components/ui/Skeleton";
import { api } from "@/services/api";
import type { CustomerSummary, Page } from "@/types/api";

const RISK_OPTS = [
  { value: "", label: "All risk levels" },
  { value: "critical", label: "Critical" },
  { value: "high", label: "High" },
  { value: "medium", label: "Medium" },
  { value: "low", label: "Low" },
];
const KYC_OPTS = [
  { value: "", label: "All KYC" },
  { value: "verified", label: "Verified" },
  { value: "pending", label: "Pending" },
  { value: "rejected", label: "Rejected" },
];

export function Customers() {
  const [q, setQ] = useState("");
  const [risk, setRisk] = useState("");
  const [kyc, setKyc] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<Page<CustomerSummary> | null>(null);
  const [loading, setLoading] = useState(true);

  // Reset to page 1 whenever a filter changes.
  useEffect(() => setPage(1), [q, risk, kyc]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    const t = setTimeout(() => {
      api
        .customers({ page, page_size: 20, q, risk_level: risk, kyc_status: kyc })
        .then((d) => active && (setData(d), setLoading(false)))
        .catch(() => active && setLoading(false));
    }, 250);
    return () => {
      active = false;
      clearTimeout(t);
    };
  }, [q, risk, kyc, page]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="space-y-4"
    >
      <div>
        <h1 className="text-lg font-semibold text-white">Customers</h1>
        <p className="text-xs text-white/40">
          {data ? `${data.total} customers` : "Loading…"}
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[220px]">
          <Search
            size={15}
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-white/30"
          />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search by name…"
            className="w-full rounded-lg border border-white/10 bg-ink-850 py-2 pl-9 pr-3 text-sm text-white/80 outline-none transition-colors hover:border-white/20 focus:border-gold-500/40"
          />
        </div>
        <Select value={risk} onChange={setRisk} options={RISK_OPTS} />
        <Select value={kyc} onChange={setKyc} options={KYC_OPTS} />
      </div>

      <Panel title="Customer Directory" icon={<Users size={16} />} bodyClassName="p-2">
        {loading && !data ? (
          <RowsSkeleton />
        ) : !data || data.items.length === 0 ? (
          <p className="p-6 text-center text-sm text-white/40">
            No customers match these filters.
          </p>
        ) : (
          <>
            <ul className="divide-y divide-white/5">
              {data.items.map((c) => (
                <li key={c.id}>
                  <Link
                    to={`/investigations/${c.id}`}
                    className="flex items-center gap-4 rounded-lg px-3 py-2.5 transition-colors hover:bg-white/5"
                  >
                    <div
                      className="grid h-9 w-9 shrink-0 place-items-center rounded-lg text-xs font-bold"
                      style={{
                        backgroundColor: `${RISK_COLORS[c.risk_level]}1f`,
                        color: RISK_COLORS[c.risk_level],
                      }}
                    >
                      {c.full_name
                        .split(" ")
                        .map((n) => n[0])
                        .slice(0, 2)
                        .join("")}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-medium text-white/90">
                        {c.full_name}
                      </div>
                      <div className="truncate text-xs text-white/40">
                        {c.occupation} · {c.city}, {c.country}
                      </div>
                    </div>
                    <Badge className="hidden border-white/10 bg-white/5 text-white/50 capitalize sm:inline-flex">
                      {c.kyc_status}
                    </Badge>
                    <RiskBadge level={c.risk_level} />
                    <span className="w-8 text-right text-sm font-bold tabular-nums text-white/80">
                      {c.risk_score ?? 0}
                    </span>
                    <ChevronRight size={16} className="text-white/25" />
                  </Link>
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
