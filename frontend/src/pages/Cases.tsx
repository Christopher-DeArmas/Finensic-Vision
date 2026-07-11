import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { CheckCircle2, ChevronRight, FolderOpen } from "lucide-react";
import { motion } from "framer-motion";
import { Panel } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { RiskBadge } from "@/components/ui/RiskBadge";
import { RowsSkeleton } from "@/components/ui/Skeleton";
import { api } from "@/services/api";
import type { CaseRead, Severity } from "@/types/api";

const OPEN = ["open", "investigating"];
const CLOSED = ["closed"];

function fmtDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function Cases({ kind }: { kind: "open" | "closed" }) {
  const [rows, setRows] = useState<CaseRead[] | null>(null);
  const open = kind === "open";

  useEffect(() => {
    setRows(null);
    api
      .cases()
      .then((p) => {
        const set = open ? OPEN : CLOSED;
        setRows(p.items.filter((c) => set.includes(c.status)));
      })
      .catch(() => setRows([]));
  }, [open]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="space-y-4"
    >
      <div>
        <h1 className="text-lg font-semibold text-white">
          {open ? "Open Cases" : "Closed Cases"}
        </h1>
        <p className="text-xs text-white/40">
          {rows ? `${rows.length} case${rows.length === 1 ? "" : "s"}` : "Loading…"}
        </p>
      </div>

      <Panel
        title={open ? "Active Investigations" : "Resolved Investigations"}
        icon={open ? <FolderOpen size={16} /> : <CheckCircle2 size={16} />}
        bodyClassName="p-2"
      >
        {rows === null ? (
          <RowsSkeleton />
        ) : rows.length === 0 ? (
          <p className="p-6 text-center text-sm text-white/40">
            {open
              ? "No open cases. Open one from a customer investigation."
              : "No closed cases yet."}
          </p>
        ) : (
          <ul className="divide-y divide-white/5">
            {rows.map((c) => (
              <li key={c.id}>
                <Link
                  to={`/cases/detail/${c.id}`}
                  className="flex items-center gap-3 rounded-lg px-3 py-3 transition-colors hover:bg-white/5"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-white/90">
                        {c.case_number}
                      </span>
                      {c.has_sar && (
                        <Badge className="border-gold-500/25 bg-gold-500/10 text-gold-300">
                          SAR filed
                        </Badge>
                      )}
                    </div>
                    <div className="truncate text-xs text-white/45">
                      {c.customer_name} ·{" "}
                      {open
                        ? `opened ${fmtDate(c.opened_at)}`
                        : `closed ${fmtDate(c.closed_at)}`}
                    </div>
                  </div>
                  <RiskBadge level={c.priority as Severity} />
                  <Badge className="hidden border-white/10 bg-white/5 text-white/50 capitalize sm:inline-flex">
                    {c.status.replace(/_/g, " ")}
                  </Badge>
                  <ChevronRight size={16} className="text-white/25" />
                </Link>
              </li>
            ))}
          </ul>
        )}
      </Panel>
    </motion.div>
  );
}
