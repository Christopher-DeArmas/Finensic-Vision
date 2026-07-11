import { Link } from "react-router-dom";
import { Flame } from "lucide-react";
import { Panel } from "@/components/ui/Card";
import { RiskBadge, RISK_COLORS } from "@/components/ui/RiskBadge";
import type { DashboardStats } from "@/types/api";

export function TopRiskCustomers({ stats }: { stats: DashboardStats }) {
  const rows = stats.top_risk_customers.slice(0, 5);

  return (
    <Panel title="Top Risk Customers" icon={<Flame size={16} />} bodyClassName="p-2 h-[300px] overflow-y-auto">
      {rows.length === 0 ? (
        <p className="p-4 text-sm text-white/40">No elevated-risk customers.</p>
      ) : (
        <ul className="divide-y divide-white/5">
          {rows.map((c, i) => {
            const score = c.risk_score ?? 0;
            return (
              <li key={c.id}>
                <Link
                  to={`/investigations/${c.id}`}
                  className="flex items-center gap-3 rounded-lg px-2 py-2.5 transition-colors hover:bg-white/5"
                >
                  <span className="w-5 text-center text-xs font-semibold text-white/30">
                    {i + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium text-white/90">
                      {c.full_name}
                    </div>
                    <div className="truncate text-xs text-white/40">
                      {c.occupation} · {c.country}
                    </div>
                  </div>
                  <div className="w-24 shrink-0">
                    <div className="mb-1 flex justify-end">
                      <RiskBadge level={c.risk_level} />
                    </div>
                    <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/5">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${score}%`,
                          backgroundColor: RISK_COLORS[c.risk_level],
                        }}
                      />
                    </div>
                  </div>
                  <span className="w-8 text-right text-sm font-bold tabular-nums text-white/80">
                    {score}
                  </span>
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </Panel>
  );
}
