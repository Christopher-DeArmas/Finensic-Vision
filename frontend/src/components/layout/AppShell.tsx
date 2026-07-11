import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import {
  Bell,
  LayoutDashboard,
  Network,
  ShieldCheck,
  Users,
} from "lucide-react";
import { cn } from "@/lib/cn";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";
import { SearchBar } from "@/components/layout/SearchBar";

const NAV = [
  { label: "Dashboard", icon: LayoutDashboard, to: "/", enabled: true },
  { label: "Investigations", icon: Network, to: "/investigations", enabled: true },
  { label: "Customers", icon: Users, to: "/customers", enabled: true },
  { label: "Alerts", icon: Bell, to: "/alerts", enabled: true },
];

function Clock() {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);
  return (
    <span className="tabular-nums text-white/50">
      {now.toLocaleTimeString("en-US", { hour12: false })} UTC
    </span>
  );
}

export function AppShell() {
  const location = useLocation();
  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col border-r border-white/5 bg-ink-900/60 px-4 py-6 backdrop-blur-sm md:flex">
        <NavLink to="/" className="flex items-center gap-2.5 px-1">
          <div className="relative">
            <div className="absolute inset-0 rounded-xl bg-brand-500/25 blur-md" />
            <img
              src="/logo.png"
              alt="Finensic Vision"
              className="relative h-10 w-10 rounded-xl object-cover"
            />
          </div>
          <div className="leading-tight">
            <div className="text-sm font-bold tracking-tight text-white">
              Finensic Vision
            </div>
            <div className="text-[10px] uppercase tracking-[0.18em] text-brand-400">
              AML Agent
            </div>
          </div>
        </NavLink>

        <nav className="mt-8 flex flex-col gap-1">
          {NAV.map(({ label, icon: Icon, to, enabled }) =>
            enabled ? (
              <NavLink
                key={label}
                to={to}
                end={to === "/"}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-gold-500/10 text-gold-300 ring-1 ring-gold-500/20"
                      : "text-white/60 hover:bg-white/5 hover:text-white",
                  )
                }
              >
                <Icon size={17} />
                {label}
              </NavLink>
            ) : (
              <span
                key={label}
                className="flex cursor-default items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-white/25"
                title="Coming soon"
              >
                <Icon size={17} />
                {label}
                <span className="ml-auto rounded bg-white/5 px-1.5 py-0.5 text-[9px] uppercase tracking-wide text-white/30">
                  Soon
                </span>
              </span>
            ),
          )}
        </nav>

        <div className="mt-auto flex items-center gap-2 rounded-lg border border-white/5 bg-ink-850/60 px-3 py-2.5 text-[11px] text-white/40">
          <ShieldCheck size={14} className="text-brand-400" />
          Synthetic demo data
        </div>
      </aside>

      {/* Main column */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-10 flex items-center justify-between border-b border-white/5 bg-ink-950/70 px-6 py-3.5 backdrop-blur-md">
          <div>
            <h1 className="text-base font-semibold tracking-tight text-white">
              AML Investigation Dashboard
            </h1>
            <p className="text-xs text-white/40">
              Real-time transaction monitoring &amp; risk analytics
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs">
            <div className="hidden md:block">
              <SearchBar />
            </div>
            <Clock />
          </div>
        </header>

        <main className="flex-1 px-6 py-6">
          <ErrorBoundary key={location.pathname}>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
}
