import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ChevronRight, Loader2, Network, TriangleAlert } from "lucide-react";
import { Panel } from "@/components/ui/Card";
import { RiskBadge, RISK_COLORS } from "@/components/ui/RiskBadge";
import { api } from "@/services/api";
import type { CustomerSummary } from "@/types/api";

export function InvestigationsList() {
  const [rows, setRows] = useState<CustomerSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .highRiskCustomers()
      .then((page) => {
        const sorted = [...page.items].sort(
          (a, b) => (b.risk_score ?? 0) - (a.risk_score ?? 0),
        );
        setRows(sorted);
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load");
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="grid h-[60vh] place-items-center text-white/40">
        <Loader2 className="animate-spin text-gold-500" size={26} />
      </div>
    );
  }
  if (error) {
    return (
      <div className="mx-auto mt-10 max-w-md">
        <div className="card flex flex-col items-center gap-3 p-8 text-center">
          <TriangleAlert className="text-risk-high" size={24} />
          <p className="text-sm text-white/70">Couldn&apos;t load investigations.</p>
          <p className="text-xs text-white/40">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold text-white">Investigations</h1>
        <p className="text-xs text-white/40">
          {rows.length} elevated-risk customer{rows.length === 1 ? "" : "s"} —
          select one to investigate.
        </p>
      </div>

      <Panel title="Elevated-Risk Customers" icon={<Network size={16} />} bodyClassName="p-2">
        {rows.length === 0 ? (
          <p className="p-4 text-sm text-white/40">
            No elevated-risk customers yet. Let the live stream run, or run a
            rescore.
          </p>
        ) : (
          <ul className="divide-y divide-white/5">
            {rows.map((c) => {
              const score = c.risk_score ?? 0;
              return (
                <li key={c.id}>
                  <Link
                    to={`/investigations/${c.id}`}
                    className="flex items-center gap-4 rounded-lg px-3 py-3 transition-colors hover:bg-white/5"
                  >
                    <div
                      className="grid h-10 w-10 shrink-0 place-items-center rounded-xl text-sm font-bold"
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
                    {c.scenario_tag && (
                      <span className="hidden rounded bg-white/5 px-2 py-0.5 text-[10px] uppercase tracking-wide text-white/40 sm:inline">
                        {c.scenario_tag.replace(/_/g, " ")}
                      </span>
                    )}
                    <RiskBadge level={c.risk_level} />
                    <span className="w-8 text-right text-sm font-bold tabular-nums text-white/80">
                      {score}
                    </span>
                    <ChevronRight size={16} className="text-white/25" />
                  </Link>
                </li>
              );
            })}
          </ul>
        )}
      </Panel>
    </div>
  );
}
