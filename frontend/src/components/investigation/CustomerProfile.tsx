import { Bell, Landmark, MapPin, ShieldAlert } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { RiskBadge, RISK_COLORS } from "@/components/ui/RiskBadge";
import { formatCurrency } from "@/lib/format";
import type { AlertRead, CustomerDetail, Severity } from "@/types/api";

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-1.5 text-sm">
      <span className="text-white/40">{label}</span>
      <span className="font-medium text-white/85">{value}</span>
    </div>
  );
}

export function CustomerProfile({
  customer,
  alerts = [],
  onAlertClick,
}: {
  customer: CustomerDetail;
  alerts?: AlertRead[];
  onAlertClick?: (a: AlertRead) => void;
}) {
  const score = customer.risk_score ?? 0;
  const color = RISK_COLORS[customer.risk_level];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <div
          className="grid h-14 w-14 shrink-0 place-items-center rounded-2xl text-lg font-bold"
          style={{ backgroundColor: `${color}1f`, color }}
        >
          {customer.full_name
            .split(" ")
            .map((n) => n[0])
            .slice(0, 2)
            .join("")}
        </div>
        <div className="min-w-0">
          <div className="truncate text-base font-semibold text-white">
            {customer.full_name}
          </div>
          <div className="truncate text-xs text-white/45">{customer.occupation}</div>
          <div className="mt-1 flex items-center gap-1.5 text-xs text-white/45">
            <MapPin size={12} /> {customer.city}, {customer.country}
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between rounded-xl border border-white/5 bg-ink-900/50 px-4 py-3">
        <div>
          <div className="stat-label">Risk Score</div>
          <div className="mt-0.5 text-2xl font-bold tabular-nums" style={{ color }}>
            {score}
            <span className="text-sm text-white/30">/100</span>
          </div>
        </div>
        <RiskBadge level={customer.risk_level} />
      </div>

      {/* Alerts — click one to review / change status (item 4) */}
      {alerts.length > 0 && (
        <div>
          <div className="stat-label mb-2 flex items-center gap-1.5">
            <Bell size={12} /> Alerts ({alerts.length})
          </div>
          <ul className="space-y-1.5">
            {alerts.map((a) => (
              <li key={a.id}>
                <button
                  onClick={() => onAlertClick?.(a)}
                  className="flex w-full items-center gap-2 rounded-lg border border-white/5 bg-ink-900/40 px-3 py-2 text-left transition-colors hover:border-gold-500/30 hover:bg-white/5"
                >
                  <span
                    className="h-2 w-2 shrink-0 rounded-full"
                    style={{ backgroundColor: RISK_COLORS[a.severity as Severity] }}
                  />
                  <span className="min-w-0 flex-1 truncate text-xs text-white/80">
                    {a.title}
                  </span>
                  <Badge className="border-white/10 bg-white/5 text-white/45 capitalize">
                    {a.status.replace(/_/g, " ")}
                  </Badge>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="flex flex-wrap gap-1.5">
        {customer.is_high_risk_jurisdiction && (
          <Badge className="border-risk-high/25 bg-risk-high/10 text-risk-high">
            <ShieldAlert size={11} /> High-risk jurisdiction
          </Badge>
        )}
        {customer.scenario_tag && (
          <Badge className="border-gold-500/25 bg-gold-500/10 text-gold-300">
            {customer.scenario_tag.replace(/_/g, " ")}
          </Badge>
        )}
        <Badge className="border-white/10 bg-white/5 text-white/55 capitalize">
          KYC: {customer.kyc_status}
        </Badge>
      </div>

      <div className="divide-y divide-white/5 border-y border-white/5">
        <Row label="Annual income" value={formatCurrency(customer.annual_income)} />
        <Row
          label="Expected / mo"
          value={formatCurrency(customer.expected_monthly_income)}
        />
        <Row label="Accounts" value={String(customer.accounts.length)} />
      </div>

      <div>
        <div className="stat-label mb-2 flex items-center gap-1.5">
          <Landmark size={12} /> Accounts
        </div>
        <ul className="space-y-1.5">
          {customer.accounts.map((a) => (
            <li
              key={a.id}
              className="flex items-center justify-between rounded-lg border border-white/5 bg-ink-900/40 px-3 py-2 text-sm"
            >
              <span className="capitalize text-white/70">
                {a.account_type}
                <span className="ml-2 text-white/30">••{a.account_number.slice(-4)}</span>
                {a.is_dormant && (
                  <span className="ml-2 text-[10px] uppercase text-risk-high">
                    dormant
                  </span>
                )}
              </span>
              <span className="font-medium tabular-nums text-white/85">
                {formatCurrency(a.balance)}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
