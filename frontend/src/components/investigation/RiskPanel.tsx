import { useState } from "react";
import {
  Check,
  Download,
  FileText,
  Loader2,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { RISK_COLORS } from "@/components/ui/RiskBadge";
import { api } from "@/services/api";
import type { AISummary, CustomerDetail, SarReportRead, Severity } from "@/types/api";

function List({ items }: { items: string[] }) {
  return (
    <ul className="space-y-1.5">
      {items.map((t, i) => (
        <li key={i} className="flex gap-2 text-xs leading-relaxed text-white/60">
          <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-brand-400" />
          {t}
        </li>
      ))}
    </ul>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="stat-label mb-1.5">{title}</div>
      {children}
    </div>
  );
}

export function RiskPanel({
  customer,
  caseId,
  initialSummary,
}: {
  customer: CustomerDetail;
  caseId?: number;
  initialSummary?: AISummary | null;
}) {
  const breakdown = customer.latest_risk?.breakdown ?? [];
  const [summary, setSummary] = useState<AISummary | null>(initialSummary ?? null);
  const [sar, setSar] = useState<SarReportRead | null>(null);
  const [busy, setBusy] = useState<"summary" | "sar" | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runSummary = async () => {
    if (!caseId) return;
    setBusy("summary");
    setError(null);
    try {
      setSummary(await api.generateSummary(caseId));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally {
      setBusy(null);
    }
  };

  const runSar = async () => {
    if (!caseId) return;
    setBusy("sar");
    setError(null);
    try {
      setSar(await api.generateSar(caseId));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="space-y-4">
      {/* AI summary — horizontal */}
      <div className="rounded-xl border border-brand-500/25 bg-brand-500/[0.07] p-4">
        <div className="mb-3 flex items-center justify-between">
          <div className="flex items-center gap-2 text-brand-400">
            <Sparkles size={15} />
            <span className="text-sm font-semibold">AI Investigation Summary</span>
          </div>
          <div className="flex items-center gap-2">
            {summary && (
              <>
                <Badge className="border-white/10 bg-white/5 text-white/50">
                  {summary.generated_by === "openai" ? "OpenAI" : "Rule-based"}
                </Badge>
                <button
                  onClick={runSummary}
                  disabled={busy !== null}
                  className="flex items-center gap-1.5 text-[11px] text-white/40 hover:text-white/70 disabled:opacity-50"
                >
                  <RefreshCw size={11} /> Regenerate
                </button>
              </>
            )}
          </div>
        </div>

        {!caseId ? (
          <p className="text-xs leading-relaxed text-white/50">
            Open a case (button above) to generate the AI investigation summary
            and Suspicious Activity Report.
          </p>
        ) : !summary ? (
          <button
            onClick={runSummary}
            disabled={busy !== null}
            className="flex items-center justify-center gap-2 rounded-lg border border-brand-500/40 bg-brand-500/15 px-4 py-2 text-xs font-medium text-brand-400 transition-colors hover:bg-brand-500/25 disabled:opacity-50"
          >
            {busy === "summary" ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <Sparkles size={14} />
            )}
            Generate AI Summary
          </button>
        ) : (
          <div className="grid gap-5 md:grid-cols-3">
            <div className="space-y-3">
              <Section title="Executive Summary">
                <p className="text-xs leading-relaxed text-white/75">
                  {summary.executive_summary}
                </p>
              </Section>
              <Section title="Key Findings">
                <List items={summary.key_findings} />
              </Section>
            </div>
            <div className="space-y-3">
              <Section title="Likely Behaviors">
                <div className="flex flex-wrap gap-1.5">
                  {summary.likely_behaviors.map((b, i) => (
                    <Badge
                      key={i}
                      className="border-brand-500/25 bg-brand-500/10 text-brand-400"
                    >
                      {b}
                    </Badge>
                  ))}
                </div>
              </Section>
              <Section title="Risk Assessment">
                <p className="text-xs leading-relaxed text-white/60">
                  {summary.risk_assessment}
                </p>
              </Section>
            </div>
            <Section title="Recommended Next Steps">
              <List items={summary.recommended_next_steps} />
            </Section>
          </div>
        )}
      </div>

      {error && <p className="text-xs text-risk-high">{error}</p>}

      {/* SAR + triggered rules side by side */}
      <div className="grid gap-4 lg:grid-cols-2">
        {caseId && (
          <div className="rounded-xl border border-white/5 bg-ink-900/40 p-4">
            <div className="flex items-center gap-2 text-white/80">
              <FileText size={15} className="text-gold-400" />
              <span className="text-sm font-semibold">
                Suspicious Activity Report
              </span>
            </div>
            {sar ? (
              <div className="mt-2 space-y-2">
                <div className="flex items-center gap-1.5 text-xs text-risk-low">
                  <Check size={13} /> Generated · {sar.reference}
                </div>
                <a
                  href={api.sarExportUrl(caseId)}
                  download
                  className="flex w-full max-w-xs items-center justify-center gap-2 rounded-lg border border-gold-500/40 bg-gold-500/10 py-2 text-xs font-medium text-gold-300 transition-colors hover:bg-gold-500/20"
                >
                  <Download size={14} /> Download SAR (PDF)
                </a>
              </div>
            ) : (
              <button
                onClick={runSar}
                disabled={busy !== null}
                className="mt-3 flex w-full max-w-xs items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/5 py-2 text-xs font-medium text-white/70 transition-colors hover:bg-white/10 disabled:opacity-50"
              >
                {busy === "sar" ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <FileText size={14} />
                )}
                Generate SAR
              </button>
            )}
          </div>
        )}

        <div className={caseId ? "" : "lg:col-span-2"}>
          <div className="stat-label mb-2">Triggered Rules</div>
          {breakdown.length === 0 ? (
            <p className="text-sm text-white/40">No rules triggered.</p>
          ) : (
            <ul className="grid gap-2.5 sm:grid-cols-2 lg:grid-cols-1">
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
    </div>
  );
}
