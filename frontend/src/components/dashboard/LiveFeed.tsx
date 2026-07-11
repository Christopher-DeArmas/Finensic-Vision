import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowDownLeft,
  ArrowRightLeft,
  ArrowUp,
  ArrowUpRight,
  Radio,
  type LucideIcon,
} from "lucide-react";
import { Panel } from "@/components/ui/Card";
import { cn } from "@/lib/cn";
import { formatCurrency, formatTime } from "@/lib/format";
import { useLiveData } from "@/contexts/LiveDataProvider";
import type { LiveTransaction } from "@/types/api";

function directionIcon(type: string): LucideIcon {
  if (type === "deposit" || type === "wire") return ArrowDownLeft;
  if (type === "transfer") return ArrowRightLeft;
  return ArrowUpRight;
}

function counterparty(t: LiveTransaction): string {
  if (t.merchant_name) return t.merchant_name;
  if (t.sender_name && t.receiver_name)
    return `${t.sender_name} → ${t.receiver_name}`;
  return t.receiver_name ?? t.sender_name ?? "—";
}

function StatusPill({ connected }: { connected: boolean }) {
  return (
    <span className="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[11px] font-medium text-white/60">
      <span
        className={cn(
          "h-1.5 w-1.5 rounded-full",
          connected ? "animate-pulseDot bg-risk-low" : "bg-white/30",
        )}
      />
      {connected ? "Live" : "Connecting…"}
    </span>
  );
}

export function LiveFeed() {
  const { transactions, connected, flaggedSeen } = useLiveData();
  const scrollRef = useRef<HTMLDivElement>(null);
  const [stuck, setStuck] = useState(true);
  const [snapshot, setSnapshot] = useState<LiveTransaction[]>([]);

  useEffect(() => {
    if (stuck) setSnapshot(transactions);
  }, [stuck, transactions]);

  const displayed = stuck ? transactions : snapshot;

  const newCount = useMemo(() => {
    if (stuck || snapshot.length === 0) return 0;
    const topId = snapshot[0]?.external_id;
    const idx = transactions.findIndex((t) => t.external_id === topId);
    return idx === -1 ? transactions.length : idx;
  }, [stuck, snapshot, transactions]);

  const onScroll = () => {
    const el = scrollRef.current;
    if (!el) return;
    const atTop = el.scrollTop <= 8;
    if (atTop !== stuck) setStuck(atTop);
  };

  const jumpToLive = () => {
    scrollRef.current?.scrollTo({ top: 0, behavior: "smooth" });
    setStuck(true);
    setSnapshot(transactions);
  };

  return (
    <Panel
      title="Live Transaction Feed"
      icon={<Radio size={16} />}
      className="h-[440px]"
      action={
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-white/35">{flaggedSeen} flagged</span>
          <StatusPill connected={connected} />
        </div>
      }
      bodyClassName="p-0"
    >
      <div className="relative flex h-full flex-col">
        <div ref={scrollRef} onScroll={onScroll} className="min-h-0 flex-1 overflow-y-auto p-2">
          {displayed.length === 0 ? (
            <div className="grid h-full place-items-center text-sm text-white/30">
              Waiting for transactions…
            </div>
          ) : (
            <ul>
              <AnimatePresence initial={false}>
                {displayed.map((t) => {
                  const Icon = directionIcon(t.transaction_type);
                  return (
                    <motion.li
                      key={t.external_id}
                      layout
                      initial={{ opacity: 0, y: -8 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.25 }}
                      className={cn(
                        "flex items-center gap-3 rounded-lg px-2.5 py-2",
                        t.is_flagged && "animate-flash border-l-2 border-risk-critical",
                      )}
                    >
                      <span
                        className={cn(
                          "grid h-7 w-7 shrink-0 place-items-center rounded-md",
                          t.is_flagged
                            ? "bg-risk-critical/15 text-risk-critical"
                            : "bg-white/5 text-white/50",
                        )}
                      >
                        <Icon size={14} />
                      </span>
                      <div className="min-w-0 flex-1">
                        <div className="truncate text-sm text-white/85">
                          {counterparty(t)}
                        </div>
                        <div className="truncate text-[11px] text-white/35">
                          {t.transaction_type} · {t.city} · {formatTime(t.timestamp)}
                        </div>
                      </div>
                      <span
                        className={cn(
                          "shrink-0 text-sm font-semibold tabular-nums",
                          t.is_flagged ? "text-risk-critical" : "text-white/80",
                        )}
                      >
                        {formatCurrency(t.amount)}
                      </span>
                    </motion.li>
                  );
                })}
              </AnimatePresence>
            </ul>
          )}
        </div>

        <AnimatePresence>
          {!stuck && newCount > 0 && (
            <motion.button
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              onClick={jumpToLive}
              className="absolute left-1/2 top-2 flex -translate-x-1/2 items-center gap-1.5 rounded-full border border-gold-500/40 bg-ink-900/90 px-3 py-1 text-xs font-medium text-gold-300 shadow-gold backdrop-blur"
            >
              <ArrowUp size={13} />
              {newCount} new
            </motion.button>
          )}
        </AnimatePresence>
      </div>
    </Panel>
  );
}
