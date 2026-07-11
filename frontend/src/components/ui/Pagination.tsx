import { ChevronLeft, ChevronRight } from "lucide-react";

export function Pagination({
  page,
  pages,
  total,
  onPage,
}: {
  page: number;
  pages: number;
  total: number;
  onPage: (p: number) => void;
}) {
  if (pages <= 1) {
    return (
      <div className="flex items-center justify-end px-1 py-2 text-xs text-white/40">
        {total} result{total === 1 ? "" : "s"}
      </div>
    );
  }
  const btn =
    "grid h-8 w-8 place-items-center rounded-lg border border-white/10 text-white/60 transition-colors hover:border-gold-500/40 hover:text-gold-300 disabled:cursor-not-allowed disabled:opacity-30";
  return (
    <div className="flex items-center justify-between px-1 py-2 text-xs text-white/40">
      <span>{total} results</span>
      <div className="flex items-center gap-2">
        <button className={btn} onClick={() => onPage(page - 1)} disabled={page <= 1}>
          <ChevronLeft size={15} />
        </button>
        <span className="tabular-nums text-white/60">
          {page} / {pages}
        </span>
        <button
          className={btn}
          onClick={() => onPage(page + 1)}
          disabled={page >= pages}
        >
          <ChevronRight size={15} />
        </button>
      </div>
    </div>
  );
}
