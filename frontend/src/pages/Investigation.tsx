import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft,
  FolderPlus,
  Loader2,
  Network,
  Sparkles,
  TriangleAlert,
} from "lucide-react";
import { Panel } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { RiskBadge } from "@/components/ui/RiskBadge";
import { CustomerProfile } from "@/components/investigation/CustomerProfile";
import { TransactionGraph } from "@/components/investigation/TransactionGraph";
import { RiskPanel } from "@/components/investigation/RiskPanel";
import { Timeline } from "@/components/investigation/Timeline";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";
import { useInvestigation } from "@/hooks/useInvestigation";
import { api } from "@/services/api";
import type { AISummary } from "@/types/api";

export function Investigation() {
  const { customerId } = useParams();
  const id = Number(customerId);
  const { bundle, loading, error, reload } = useInvestigation(id);
  const [opening, setOpening] = useState(false);

  if (loading && !bundle) {
    return (
      <div className="grid h-[70vh] place-items-center text-white/40">
        <Loader2 className="animate-spin text-gold-500" size={28} />
      </div>
    );
  }
  if (error || !bundle) {
    return (
      <div className="mx-auto mt-10 max-w-md">
        <div className="card flex flex-col items-center gap-3 p-8 text-center">
          <TriangleAlert className="text-risk-high" size={26} />
          <p className="text-sm text-white/70">Couldn&apos;t load this investigation.</p>
          <p className="text-xs text-white/40">{error}</p>
          <Link to="/" className="text-xs text-gold-400 hover:underline">
            ← Back to dashboard
          </Link>
        </div>
      </div>
    );
  }

  const { customer, alerts, cases, graph, timeline } = bundle;
  const openCase = cases[0];

  const handleOpenCase = async () => {
    if (!alerts[0]) return;
    setOpening(true);
    try {
      await api.openCase(alerts[0].id);
      await reload();
    } finally {
      setOpening(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Link
            to="/"
            className="grid h-8 w-8 place-items-center rounded-lg border border-white/10 text-white/60 transition-colors hover:border-gold-500/40 hover:text-gold-300"
          >
            <ArrowLeft size={16} />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-semibold text-white">
                {customer.full_name}
              </h1>
              <RiskBadge level={customer.risk_level} />
            </div>
            <p className="text-xs text-white/40">
              Investigation · {alerts.length} alert
              {alerts.length === 1 ? "" : "s"}
            </p>
          </div>
        </div>

        {openCase ? (
          <Badge className="border-gold-500/25 bg-gold-500/10 text-gold-300">
            {openCase.case_number} · {openCase.status}
          </Badge>
        ) : (
          <button
            onClick={handleOpenCase}
            disabled={opening || alerts.length === 0}
            className="flex items-center gap-2 rounded-lg border border-gold-500/40 bg-gold-500/10 px-3.5 py-2 text-sm font-medium text-gold-300 transition-colors hover:bg-gold-500/20 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {opening ? (
              <Loader2 size={15} className="animate-spin" />
            ) : (
              <FolderPlus size={15} />
            )}
            Open Case
          </button>
        )}
      </div>

      {/* Top row: customer / graph / timeline */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        <div className="lg:col-span-3">
          <Panel title="Customer">
            <CustomerProfile customer={customer} />
          </Panel>
        </div>

        <div className="lg:col-span-6">
          <Panel
            title="Transaction Network"
            icon={<Network size={16} />}
            bodyClassName="p-0"
          >
            <div className="h-[460px] w-full">
              <ErrorBoundary
                fallback={
                  <div className="grid h-full place-items-center text-sm text-white/40">
                    Graph unavailable
                  </div>
                }
              >
                <TransactionGraph graph={graph} />
              </ErrorBoundary>
            </div>
          </Panel>
        </div>

        <div className="lg:col-span-3">
          <Panel
            title="Investigation Timeline"
            bodyClassName="max-h-[460px] overflow-y-auto"
          >
            <Timeline events={timeline} />
          </Panel>
        </div>
      </div>

      {/* AI investigation — full width, horizontal */}
      <Panel title="AI Investigation" icon={<Sparkles size={16} />}>
        <RiskPanel
          customer={customer}
          caseId={openCase?.id}
          initialSummary={(openCase?.ai_summary as AISummary | null) ?? null}
        />
      </Panel>
    </div>
  );
}
