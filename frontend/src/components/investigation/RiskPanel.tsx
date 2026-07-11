import { Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { RISK_COLORS } from "@/components/ui/RiskBadge";
import type { CustomerDetail, Severity } from "@/types/api";

export function RiskPanel({ customer }: { customer: CustomerDetail }) {
  const breakdown = customer.latest_risk?.breakdown ?? [];

  return (
    <div className="space-y-4">
      {/* AI summary placeholder (wired up in Stage 7). */}
      <div className="rounded-xl border border-brand-500/25 bg-brand-500/[0.07] p-4">
        <div className="flex items-center gap-2 text-brand-400">
          <Sparkles size={15} />
          <span className="text-sm font-semibold">AI Investigation Summary</span>
        </div>
        <p className="mt-2 text-xs leading-relaxed text-white/50">
          An OpenAI-generated executive summary, key findings, and recommended
          next steps will appear here.
        </p>
        <button
          disabled
          className="mt-3 w-full cursor-not-allowed rounded-lg border border-white/10 bg-white/5 py-2 text-xs font-medium text-white/40"
        >
          Generate AI Summary · Stage 7
        </button>
      </div>

      <div>
        <div className="stat-label mb-2">Triggered Rules</div>
        {breakdown.length === 0 ? (
          <p className="text-sm text-white/40">No rules triggered.</p>
        ) : (
          <ul className="space-y-2.5">
            {breakdown.map((b) => {
              const c = RISK_COLORS[b.severity as Severity] ?? "#d4af37";
              return (
                <li
                  key={b.rule}
                  className="rounded-lg border border-white/5 bg-ink-900/40 p-3"
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Badge className="border-white/10 bg-white/5 text-white/60">
                        {b.rule}
                      </Badge>
                      <span className="text-sm font-medium text-white/85">
                        {b.name}
                      </span>
                    </div>
                    <span
                      className="text-sm font-bold tabular-nums"
                      style={{ color: c }}
                    >
                      +{b.points}
                    </span>
                  </div>
                  <p className="mt-1.5 text-xs leading-relaxed text-white/50">
                    {b.reason}
                  </p>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}
