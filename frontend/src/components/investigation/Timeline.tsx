import {
  AlertTriangle,
  ArrowLeftRight,
  FolderOpen,
  UserPlus,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/cn";
import { RISK_COLORS } from "@/components/ui/RiskBadge";
import { formatCurrency } from "@/lib/format";
import type { Severity, TimelineEvent } from "@/types/api";

const ICONS: Record<TimelineEvent["type"], LucideIcon> = {
  account_opened: UserPlus,
  transaction: ArrowLeftRight,
  alert: AlertTriangle,
  case_opened: FolderOpen,
};

function color(e: TimelineEvent): string {
  if (e.type === "transaction") return e.flagged ? "#ef4444" : "#d4af37";
  if (e.severity) return RISK_COLORS[e.severity as Severity] ?? "#d4af37";
  return "#8a8a92";
}

function stamp(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function Timeline({
  events,
  selectedId,
  onSelect,
}: {
  events: TimelineEvent[];
  selectedId?: number | null;
  onSelect?: (id: number | null) => void;
}) {
  if (events.length === 0) {
    return <p className="p-4 text-sm text-white/40">No timeline events.</p>;
  }
  return (
    <ol className="relative ml-2 border-l border-white/10">
      {events.map((e) => {
        const Icon = ICONS[e.type];
        const c = color(e);
        const txnId =
          e.type === "transaction" ? Number(e.id.replace("txn-", "")) : null;
        const clickable = txnId != null && !!onSelect;
        const isSel = clickable && selectedId === txnId;
        return (
          <li
            key={e.id}
            onClick={
              clickable ? () => onSelect!(isSel ? null : txnId) : undefined
            }
            className={cn(
              "mb-4 ml-5 rounded-lg last:mb-0",
              clickable &&
                "-mx-2 cursor-pointer px-2 py-1 transition-colors hover:bg-white/5",
              isSel && "bg-gold-500/10 ring-1 ring-gold-500/30",
            )}
          >
            <span
              className="absolute -left-[11px] grid h-[22px] w-[22px] place-items-center rounded-full ring-4 ring-ink-850"
              style={{ backgroundColor: `${c}22`, color: c }}
            >
              <Icon size={12} />
            </span>
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-medium text-white/90">{e.title}</p>
              <time className="shrink-0 text-[11px] tabular-nums text-white/35">
                {stamp(e.timestamp)}
              </time>
            </div>
            {e.description && (
              <p className="mt-0.5 text-xs text-white/45">{e.description}</p>
            )}
            {e.amount != null && (
              <span
                className="mt-1 inline-block text-xs font-semibold tabular-nums"
                style={{ color: c }}
              >
                {formatCurrency(e.amount)}
              </span>
            )}
          </li>
        );
      })}
    </ol>
  );
}
