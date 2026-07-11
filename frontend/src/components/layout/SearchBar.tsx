import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, X } from "lucide-react";
import { RiskBadge } from "@/components/ui/RiskBadge";
import { api } from "@/services/api";
import type { SearchResults } from "@/types/api";

export function SearchBar() {
  const [q, setQ] = useState("");
  const [results, setResults] = useState<SearchResults | null>(null);
  const [open, setOpen] = useState(false);
  const boxRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (q.trim().length < 1) {
      setResults(null);
      return;
    }
    let active = true;
    const t = setTimeout(() => {
      api
        .search(q.trim())
        .then((r) => active && (setResults(r), setOpen(true)))
        .catch(() => {});
    }, 220);
    return () => {
      active = false;
      clearTimeout(t);
    };
  }, [q]);

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (boxRef.current && !boxRef.current.contains(e.target as Node))
        setOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const go = (path: string) => {
    setOpen(false);
    setQ("");
    navigate(path);
  };

  const empty =
    results &&
    !results.customers.length &&
    !results.accounts.length &&
    !results.merchants.length &&
    !results.transactions.length;

  return (
    <div ref={boxRef} className="relative w-64">
      <Search
        size={15}
        className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-white/30"
      />
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        onFocus={() => results && setOpen(true)}
        placeholder="Search customers"
        className="w-full rounded-lg border border-white/10 bg-ink-850/80 py-1.5 pl-9 pr-8 text-sm text-white/80 outline-none transition-colors focus:border-gold-500/40"
      />
      {q && (
        <button
          onClick={() => {
            setQ("");
            setResults(null);
          }}
          className="absolute right-2 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60"
        >
          <X size={14} />
        </button>
      )}

      {open && results && (
        <div className="absolute right-0 z-20 mt-2 max-h-96 w-80 overflow-auto rounded-xl border border-white/10 bg-ink-900/95 p-2 shadow-card backdrop-blur">
          {empty && (
            <p className="p-3 text-center text-xs text-white/40">No matches.</p>
          )}
          {results.customers.length > 0 && (
            <div className="mb-1">
              <div className="stat-label px-2 py-1">Customers</div>
              {results.customers.map((c) => (
                <button
                  key={c.id}
                  onClick={() => go(`/investigations/${c.id}`)}
                  className="flex w-full items-center justify-between gap-2 rounded-lg px-2 py-1.5 text-left text-sm text-white/80 hover:bg-white/5"
                >
                  <span className="truncate">{c.name}</span>
                  <RiskBadge level={c.risk_level} />
                </button>
              ))}
            </div>
          )}
          {results.merchants.length > 0 && (
            <div className="mb-1">
              <div className="stat-label px-2 py-1">Merchants</div>
              {results.merchants.map((m) => (
                <div
                  key={m.id}
                  className="flex items-center justify-between px-2 py-1.5 text-sm text-white/70"
                >
                  <span className="truncate">{m.name}</span>
                  <span className="text-[11px] text-white/35">{m.category}</span>
                </div>
              ))}
            </div>
          )}
          {results.accounts.length > 0 && (
            <div className="mb-1">
              <div className="stat-label px-2 py-1">Accounts</div>
              {results.accounts.map((a) => (
                <div
                  key={a.id}
                  className="flex items-center justify-between px-2 py-1.5 text-sm text-white/70"
                >
                  <span className="truncate">••{a.account_number.slice(-6)}</span>
                  <span className="text-[11px] text-white/35">{a.type}</span>
                </div>
              ))}
            </div>
          )}
          {results.transactions.length > 0 && (
            <div>
              <div className="stat-label px-2 py-1">Transactions</div>
              {results.transactions.map((t) => (
                <div
                  key={t.id}
                  className="flex items-center justify-between px-2 py-1.5 text-sm text-white/70"
                >
                  <span className="truncate">{t.external_id}</span>
                  <span className="text-[11px] tabular-nums text-white/35">
                    ${t.amount.toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
