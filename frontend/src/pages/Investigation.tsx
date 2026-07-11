import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  FolderPlus,
  Loader2,
  Lock,
  Network,
  Sparkles,
  TriangleAlert,
  X,
} from "lucide-react";
import { Panel } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { RiskBadge, RISK_COLORS } from "@/components/ui/RiskBadge";
import { CustomerProfile } from "@/components/investigation/CustomerProfile";
import { TransactionGraph } from "@/components/investigation/TransactionGraph";
import { RiskPanel } from "@/components/investigation/RiskPanel";
import { Timeline } from "@/components/investigation/Timeline";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";
import { useInvestigation } from "@/hooks/useInvestigation";
import { relativeTime } from "@/lib/format";
import { api } from "@/services/api";
import type { AISummary, AlertRead, Severity } from "@/types/api";

const STATUS_OPTS = ["open", "in_review", "escalated", "dismissed"];

const RULE_NAMES: Record<string, string> = {
  "AML-01": "Structuring",
  "AML-02": "Rapid Fund Movement",
  "AML-03": "Circular Transfers",
  "AML-04": "Dormant Account Awakening",
  "AML-05": "High Transaction Velocity",
  "AML-06": "Geographic Anomaly",
  "AML-07": "Multiple Incoming Sources",
  "AML-08": "High-Risk Jurisdiction",
  "AML-09": "Large Cash Deposit",
  "AML-10": "Account Explosion",
};

export function Investigation() {
  const { customerId } = useParams();
  const id = Number(customerId);
  const navigate = useNavigate();
  const { bundle, loading, error, reload } = useInvestigation(id);
  const [opening, setOpening] = useState(false);
  const [highlightTxn, setHighlightTxn] = useState<number | null>(null);
  const [hoverTxn, setHoverTxn] = useState<number | null>(null);
  const [alertModal, setAlertModal] = useState<AlertRead | null>(null);
  const [closeOpen, setCloseOpen] = useState(false);
  const [closeText, setCloseText] = useState("");
  const [closing, setClosing] = useState(false);

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
  const caseClosed = openCase?.status === "closed";

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

  const changeAlertStatus = async (alert: AlertRead, status: string) => {
    await api.updateAlert(alert.id, status);
    setAlertModal({ ...alert, status });
    await reload();
  };

  const handleCloseCase = async () => {
    if (!openCase || closeText.trim() !== "Close Case") return;
    setClosing(true);
    try {
      await api.updateCase(openCase.id, { status: "closed" });
      setCloseOpen(false);
      setCloseText("");
      await reload();
    } finally {
      setClosing(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="grid h-8 w-8 place-items-center rounded-lg border border-white/10 text-white/60 transition-colors hover:border-gold-500/40 hover:text-gold-300"
          >
            <ArrowLeft size={16} />
          </button>
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

        <div className="flex items-center gap-2">
          {openCase ? (
            <>
              <Badge className="border-gold-500/25 bg-gold-500/10 text-gold-300">
                {openCase.case_number} · {openCase.status.replace(/_/g, " ")}
              </Badge>
              {!caseClosed && (
                <button
                  onClick={() => setCloseOpen(true)}
                  className="flex items-center gap-2 rounded-lg border border-risk-critical/40 bg-risk-critical/10 px-3 py-2 text-sm font-medium text-risk-critical transition-colors hover:bg-risk-critical/20"
                >
                  <Lock size={14} /> Close Case
                </button>
              )}
            </>
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
      </div>

      {/* Top row: customer / graph / timeline */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        <div className="lg:col-span-3">
          <Panel title="Customer">
            <CustomerProfile
              customer={customer}
              alerts={alerts}
              onAlertClick={setAlertModal}
            />
          </Panel>
        </div>

        <div className="lg:col-span-6">
          <Panel title="Transaction Network" icon={<Network size={16} />} bodyClassName="p-0">
            <div className="h-[460px] w-full">
              <ErrorBoundary
                fallback={
                  <div className="grid h-full place-items-center text-sm text-white/40">
                    Graph unavailable
                  </div>
                }
              >
                <TransactionGraph
                  graph={graph}
                  highlightTxnId={hoverTxn ?? highlightTxn}
                  onEdgeHover={setHoverTxn}
                />
              </ErrorBoundary>
            </div>
          </Panel>
        </div>

        <div className="lg:col-span-3">
          <Panel title="Investigation Timeline" bodyClassName="max-h-[460px] overflow-y-auto">
            <Timeline
              events={timeline}
              selectedId={hoverTxn ?? highlightTxn}
              onSelect={setHighlightTxn}
            />
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

      {/* Alert review modal (item 4) */}
      {alertModal && (
        <div
          className="fixed inset-0 z-40 grid place-items-center bg-black/60 p-4 backdrop-blur-sm"
          onClick={() => setAlertModal(null)}
        >
          <div
            className="card w-full max-w-md p-5"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-2">
                <span
                  className="h-2.5 w-2.5 rounded-full"
                  style={{
                    backgroundColor: RISK_COLORS[alertModal.severity as Severity],
                  }}
                />
                <h3 className="text-sm font-semibold text-white">
                  {alertModal.title}
                </h3>
              </div>
              <button
                onClick={() => setAlertModal(null)}
                className="text-white/40 hover:text-white/70"
              >
                <X size={16} />
              </button>
            </div>
            <div className="mt-4 border-t border-white/5 pt-4">
              <div className="stat-label mb-1.5">Description</div>
              <p className="text-xs leading-relaxed text-white/60">
                {alertModal.description}
              </p>
            </div>

            <div className="mt-4 border-t border-white/5 pt-4">
              <div className="stat-label mb-1.5">Triggered rules</div>
              <div className="space-y-1.5">
                {alertModal.triggered_rules.map((r) => (
                  <div
                    key={r}
                    className="flex items-center gap-2.5 rounded-lg border border-white/5 bg-ink-900/50 px-3 py-2"
                  >
                    <Badge className="shrink-0 border-white/10 bg-white/5 text-white/60">
                      {r}
                    </Badge>
                    <span className="text-xs text-white/70">
                      {RULE_NAMES[r] ?? r}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-4 border-t border-white/5 pt-4">
              <div className="stat-label mb-1.5">Details</div>
              <div className="flex items-center justify-between rounded-lg border border-white/5 bg-ink-900/50 px-3 py-2 text-xs">
                <span className="text-white/40">
                  Score {alertModal.score} · {relativeTime(alertModal.created_at)}
                </span>
                <RiskBadge level={alertModal.severity} />
              </div>
            </div>

            <div className="mt-4 border-t border-white/5 pt-4">
              <div className="stat-label mb-1.5">Status</div>
              <select
                value={alertModal.status}
                onChange={(e) => changeAlertStatus(alertModal, e.target.value)}
                className="w-full rounded-lg border border-white/10 bg-ink-850 px-3 py-2 text-sm capitalize text-white/80 outline-none focus:border-gold-500/40"
              >
                {STATUS_OPTS.map((s) => (
                  <option key={s} value={s} className="bg-ink-850">
                    {s.replace(/_/g, " ")}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Close-case confirmation modal (item 11) */}
      {closeOpen && openCase && (
        <div
          className="fixed inset-0 z-40 grid place-items-center bg-black/60 p-4 backdrop-blur-sm"
          onClick={() => setCloseOpen(false)}
        >
          <div className="card w-full max-w-md p-5" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center gap-2 text-risk-critical">
              <Lock size={16} />
              <h3 className="text-sm font-semibold">Close case {openCase.case_number}?</h3>
            </div>
            <p className="mt-2 text-xs leading-relaxed text-white/55">
              This resolves and archives the investigation.
            </p>
            <p className="mt-1.5 text-xs leading-relaxed text-white/55">
              To confirm, type{" "}
              <span className="font-semibold text-white/80">Close Case</span> below.
            </p>
            <input
              autoFocus
              value={closeText}
              onChange={(e) => setCloseText(e.target.value)}
              placeholder="Close Case"
              className="mt-3 w-full rounded-lg border border-white/10 bg-ink-850 px-3 py-2 text-sm text-white/80 outline-none focus:border-risk-critical/40"
            />
            <div className="mt-4 flex justify-end gap-2">
              <button
                onClick={() => setCloseOpen(false)}
                className="rounded-lg border border-white/10 px-3 py-2 text-sm text-white/60 hover:bg-white/5"
              >
                Cancel
              </button>
              <button
                onClick={handleCloseCase}
                disabled={closeText.trim() !== "Close Case" || closing}
                className="flex items-center gap-2 rounded-lg border border-risk-critical/40 bg-risk-critical/15 px-3.5 py-2 text-sm font-medium text-risk-critical transition-colors hover:bg-risk-critical/25 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {closing ? <Loader2 size={14} className="animate-spin" /> : <Lock size={14} />}
                Close Case
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
