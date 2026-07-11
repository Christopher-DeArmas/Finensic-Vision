import { useEffect, useMemo, useRef, useState } from "react";
import {
  Check,
  ChevronDown,
  Download,
  FileText,
  Landmark,
  Loader2,
  Receipt,
  RefreshCw,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { RISK_COLORS } from "@/components/ui/RiskBadge";
import { cn } from "@/lib/cn";
import { api } from "@/services/api";
import type {
  AISummary,
  CustomerDetail,
  SarCitation,
  SarReportRead,
  Severity,
} from "@/types/api";

const MARKER_RE = /(\[[RT]\d+\])/g;

/** Render narrative text with inline [R#]/[T#] markers as clickable chips. */
function Cited({
  text,
  ids,
  active,
  onCite,
}: {
  text: string;
  ids: Set<string>;
  active: string | null;
  onCite: (id: string) => void;
}) {
  const parts = text.split(MARKER_RE);
  return (
    <p className="text-xs leading-relaxed text-white/75">
      {parts.map((part, i) => {
        const m = /^\[([RT]\d+)\]$/.exec(part);
        if (m && ids.has(m[1])) {
          const id = m[1];
          return (
            <button
              key={i}
              onClick={() => onCite(id)}
              className={cn(
                "mx-0.5 inline-flex -translate-y-px items-center rounded px-1 text-[10px] font-bold align-baseline transition-colors",
                id.startsWith("R")
                  ? "bg-brand-500/20 text-brand-300 hover:bg-brand-500/35"
                  : "bg-gold-500/20 text-gold-300 hover:bg-gold-500/35",
                active === id && "ring-1 ring-white/60",
              )}
            >
              {id}
            </button>
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </p>
  );
}

function SarNarrative({ sar }: { sar: SarReportRead }) {
  const citations = sar.citations ?? [];
  const ids = useMemo(() => new Set(citations.map((c) => c.id)), [citations]);
  const [active, setActive] = useState<string | null>(null);
  const rowRefs = useRef<Record<string, HTMLLIElement | null>>({});

  const onCite = (id: string) => {
    setActive(id);
    rowRefs.current[id]?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    window.setTimeout(() => setActive((a) => (a === id ? null : a)), 1600);
  };

  const sections: [string, string][] = [
    ["Summary", sar.summary],
    ["Reason for Suspicion", sar.reason],
    ["Recommendation", sar.recommendation],
  ];

  return (
    <div className="mt-3 grid gap-4 rounded-xl border border-white/5 bg-ink-900/40 p-4 lg:grid-cols-5">
      <div className="space-y-3 lg:col-span-3">
        {sections.map(([title, body]) => (
          <div key={title}>
            <div className="stat-label mb-1">{title}</div>
            <Cited text={body} ids={ids} active={active} onCite={onCite} />
          </div>
        ))}
      </div>
      <div className="lg:col-span-2">
        <div className="mb-1.5 flex items-center gap-1.5 text-white/70">
          <ShieldCheck size={13} className="text-brand-400" />
          <span className="stat-label !mb-0">
            Citation Trail · {citations.length}
          </span>
        </div>
        <ul className="max-h-72 space-y-1.5 overflow-y-auto pr-1">
          {citations.map((c: SarCitation) => {
            const isRule = c.kind === "rule";
            const Icon = isRule ? Landmark : Receipt;
            return (
              <li
                key={c.id}
                ref={(el) => (rowRefs.current[c.id] = el)}
                className={cn(
                  "flex gap-2 rounded-lg border p-2 transition-colors",
                  active === c.id
                    ? "border-white/40 bg-white/10"
                    : "border-white/5 bg-ink-900/50",
                )}
              >
                <span
                  className={cn(
                    "mt-0.5 grid h-5 shrink-0 place-items-center rounded px-1 text-[10px] font-bold",
                    isRule
                      ? "bg-brand-500/20 text-brand-300"
                      : "bg-gold-500/20 text-gold-300",
                  )}
                >
                  {c.id}
                </span>
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5 text-[11px] font-semibold text-white/80">
                    <Icon size={11} className="shrink-0 text-white/40" />
                    <span className="truncate">{c.label}</span>
                  </div>
                  <p className="mt-0.5 text-[11px] leading-snug text-white/50">
                    {c.detail}
                  </p>
                </div>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}

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
  const [showNarrative, setShowNarrative] = useState(false);

  // If a SAR already exists for this case, show Download instead of Generate.
  useEffect(() => {
    if (!caseId) return;
    let active = true;
    api
      .getSar(caseId)
      .then((s) => active && setSar(s))
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [caseId]);

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
            You must open a case on this customer in order to generate the AI
            powered Investigation Summary and Suspicious Activity Report.
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
                  <Check size={13} /> Generated · {sar.reference} ·{" "}
                  {sar.citations?.length ?? 0} citations
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <a
                    href={api.sarExportUrl(caseId)}
                    download
                    className="flex items-center justify-center gap-2 rounded-lg border border-gold-500/40 bg-gold-500/10 px-3 py-2 text-xs font-medium text-gold-300 transition-colors hover:bg-gold-500/20"
                  >
                    <Download size={14} /> Download SAR (PDF)
                  </a>
                  <button
                    onClick={() => setShowNarrative((v) => !v)}
                    className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs font-medium text-white/70 transition-colors hover:bg-white/10"
                  >
                    <ShieldCheck size={14} className="text-brand-400" />
                    {showNarrative ? "Hide" : "View"} narrative &amp; citations
                    <ChevronDown
                      size={13}
                      className={cn(
                        "transition-transform",
                        showNarrative && "rotate-180",
                      )}
                    />
                  </button>
                </div>
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

      {/* Citation-linked SAR narrative — each claim traces to numbered evidence */}
      {caseId && sar && showNarrative && <SarNarrative sar={sar} />}
    </div>
  );
}
