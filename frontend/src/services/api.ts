import type {
  AISummary,
  AlertRead,
  CaseRead,
  CustomerSummary,
  DashboardStats,
  InvestigationBundle,
  Page,
  SarReportRead,
  SearchResults,
} from "@/types/api";

const BASE = import.meta.env.VITE_API_BASE ?? "";

type QueryValue = string | number | boolean | undefined;

function qs(params: Record<string, QueryValue>): string {
  const s = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== "" && v !== false)
    .map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`)
    .join("&");
  return s ? `?${s}` : "";
}

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { Accept: "application/json" },
  });
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status} ${res.statusText}`);
  }
  return (await res.json()) as T;
}

async function postJSON<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status} ${res.statusText}`);
  }
  return (await res.json()) as T;
}

async function patchJSON<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status} ${res.statusText}`);
  }
  return (await res.json()) as T;
}

export interface CustomerQuery {
  page?: number;
  page_size?: number;
  q?: string;
  risk_level?: string;
  kyc_status?: string;
  high_risk_only?: boolean;
}

export interface AlertQuery {
  page?: number;
  page_size?: number;
  severity?: string;
  status?: string;
  rule?: string;
  sort?: string;
}

export const api = {
  dashboardStats: () => getJSON<DashboardStats>("/api/dashboard/stats"),
  investigation: (customerId: number) =>
    getJSON<InvestigationBundle>(`/api/investigations/${customerId}`),
  customers: (p: CustomerQuery = {}) =>
    getJSON<Page<CustomerSummary>>(`/api/customers${qs(p as Record<string, QueryValue>)}`),
  highRiskCustomers: () =>
    getJSON<Page<CustomerSummary>>(
      "/api/customers?high_risk_only=true&page_size=100",
    ),
  alerts: (p: AlertQuery = {}) =>
    getJSON<Page<AlertRead>>(`/api/alerts${qs(p as Record<string, QueryValue>)}`),
  updateAlert: (id: number, status: string) =>
    patchJSON<AlertRead>(`/api/alerts/${id}`, { status }),
  search: (q: string) => getJSON<SearchResults>(`/api/search${qs({ q })}`),
  openCase: (alertId: number) =>
    postJSON<CaseRead>("/api/cases", { alert_id: alertId }),
  generateSummary: (caseId: number) =>
    postJSON<AISummary>(`/api/cases/${caseId}/summary`, {}),
  generateSar: (caseId: number) =>
    postJSON<SarReportRead>(`/api/cases/${caseId}/sar`, {}),
  sarExportUrl: (caseId: number) => `${BASE}/api/cases/${caseId}/sar/export`,
  cases: () => getJSON<Page<CaseRead>>("/api/cases?page_size=200"),
  case: (id: number) => getJSON<CaseRead>(`/api/cases/${id}`),
  updateCase: (id: number, body: { status?: string; analyst_notes?: string }) =>
    patchJSON<CaseRead>(`/api/cases/${id}`, body),
  getSar: (caseId: number) =>
    getJSON<SarReportRead>(`/api/cases/${caseId}/sar`),
};
