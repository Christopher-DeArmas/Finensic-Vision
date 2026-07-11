import type {
  AISummary,
  CaseRead,
  CustomerSummary,
  DashboardStats,
  InvestigationBundle,
  Page,
  SarReportRead,
} from "@/types/api";

const BASE = import.meta.env.VITE_API_BASE ?? "";

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

export const api = {
  dashboardStats: () => getJSON<DashboardStats>("/api/dashboard/stats"),
  investigation: (customerId: number) =>
    getJSON<InvestigationBundle>(`/api/investigations/${customerId}`),
  highRiskCustomers: () =>
    getJSON<Page<CustomerSummary>>(
      "/api/customers?high_risk_only=true&page_size=100",
    ),
  openCase: (alertId: number) =>
    postJSON<CaseRead>("/api/cases", { alert_id: alertId }),
  generateSummary: (caseId: number) =>
    postJSON<AISummary>(`/api/cases/${caseId}/summary`, {}),
  generateSar: (caseId: number) =>
    postJSON<SarReportRead>(`/api/cases/${caseId}/sar`, {}),
  sarExportUrl: (caseId: number) => `${BASE}/api/cases/${caseId}/sar/export`,
};
