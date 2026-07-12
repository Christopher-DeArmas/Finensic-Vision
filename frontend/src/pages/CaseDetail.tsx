import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  CalendarClock,
  Download,
  FileText,
  Loader2,
  Sparkles,
  User,
} from "lucide-react";
import { Panel } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { RiskBadge } from "@/components/ui/RiskBadge";
import { api } from "@/services/api";
import { parseApiDate } from "@/lib/format";
import type { AISummary, CaseRead, Severity } from "@/types/api";

function fmt(iso: string | null): string {
  if (!iso) return "—";
  return parseApiDate(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function CaseDetail() {
  const { caseId } = useParams();
  const id = Number(caseId);
  const navigate = useNavigate();
  const [c, setC] = useState<CaseRead | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .case(id)
      .then((data) => setC(data))
      .catch(() => setC(null))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="grid h-[60vh] place-items-center text-white/40">
        <Loader2 className="animate-spin text-gold-500" size={26} />
      </div>
    );
  }
  if (!c) {
    return (
      <div className="mx-auto mt-10 max-w-md text-center text-sm text-white/50">
        Case not found.
      </div>
    );
  }

  const summary = c.ai_summary as unknown as AISummary | null;
  const closed = c.status === "closed" || c.status === "filed_sar";

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate(-1)}
          className="grid h-8 w-8 place-items-center rounded-lg border border-white/10 text-white/60 transition-colors hover:border-gold-500/40 hover:text-gold-300"
        >
          <ArrowLeft size={16} />
        </button>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-semibold text-white">{c.case_number}</h1>
            <RiskBadge level={c.priority as Severity} />
            <Badge className="border-white/10 bg-white/5 text-white/55 capitalize">
              {c.status.replace(/_/g, " ")}
            </Badge>
          </div>
          <p className="text-xs text-white/40">{c.title}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Panel title="Case" icon={<CalendarClock size={16} />}>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-white/40">Subject</span>
              <Link
                to={`/investigations/${c.customer_id}`}
                className="flex items-center gap-1 font-medium text-gold-300 hover:underline"
              >
                <User size={12} /> {c.customer_name}
              </Link>
            </div>
            <div className="flex justify-between">
              <span className="text-white/40">Opened</span>
              <span className="text-white/80">{fmt(c.opened_at)}</span>
            </div>
            {closed && (
              <div className="flex justify-between">
                <span className="text-white/40">Closed</span>
                <span className="text-white/80">{fmt(c.closed_at)}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-white/40">Transactions</span>
              <span className="text-white/80">{c.transaction_count}</span>
            </div>
          </div>

          <div className="mt-4 border-t border-white/5 pt-4">
            <div className="stat-label mb-2 flex items-center gap-1.5">
              <FileText size={12} /> Suspicious Activity Report
            </div>
            {c.has_sar ? (
              <a
                href={api.sarExportUrl(c.id)}
                download
                className="flex w-full items-center justify-center gap-2 rounded-lg border border-gold-500/40 bg-gold-500/10 py-2 text-xs font-medium text-gold-300 hover:bg-gold-500/20"
              >
                <Download size={14} /> Download SAR (PDF)
              </a>
            ) : (
              <p className="text-xs text-white/40">No SAR generated for this case.</p>
            )}
          </div>
        </Panel>

        <div className="lg:col-span-2">
          <Panel title="AI Investigation Summary" icon={<Sparkles size={16} />}>
            {summary ? (
              <div className="space-y-4">
                <p className="text-sm leading-relaxed text-white/75">
                  {summary.executive_summary}
                </p>
                <div>
                  <div className="stat-label mb-1.5">Suggested Action</div>
                  <ul className="space-y-1.5">
                    {summary.recommended_next_steps.map((s, i) => (
                      <li
                        key={i}
                        className="flex gap-2 text-xs leading-relaxed text-white/60"
                      >
                        <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-brand-400" />
                        {s}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : (
              <p className="text-sm text-white/40">
                No AI summary was generated for this case.
              </p>
            )}
          </Panel>
        </div>
      </div>
    </div>
  );
}
