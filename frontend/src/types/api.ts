// TypeScript mirrors of the backend Pydantic schemas + live WS event shapes.

export type RiskLevel = "low" | "medium" | "high" | "critical";
export type Severity = "low" | "medium" | "high" | "critical";

export interface HeatPoint {
  latitude: number;
  longitude: number;
  amount: number;
  country: string;
  is_flagged: boolean;
}

export interface CustomerSummary {
  id: number;
  full_name: string;
  occupation: string;
  country: string;
  city: string;
  risk_level: RiskLevel;
  kyc_status: string;
  is_high_risk_jurisdiction: boolean;
  scenario_tag: string | null;
  risk_score: number | null;
}

export interface AlertRead {
  id: number;
  customer_id: number;
  customer_name: string | null;
  title: string;
  description: string;
  severity: Severity;
  score: number;
  triggered_rules: string[];
  status: string;
  created_at: string;
  transaction_count: number;
}

export interface DashboardStats {
  total_customers: number;
  total_accounts: number;
  total_transactions: number;
  todays_transactions: number;
  open_cases: number;
  critical_cases: number;
  open_alerts: number;
  risk_distribution: Record<RiskLevel, number>;
  top_risk_customers: CustomerSummary[];
  recent_alerts: AlertRead[];
  heatmap: HeatPoint[];
}

// --- Live WebSocket events ---

export interface LiveTransaction {
  external_id: string;
  timestamp: string;
  amount: number;
  currency: string;
  transaction_type: string;
  payment_method: string;
  country: string;
  city: string;
  latitude: number;
  longitude: number;
  is_flagged: boolean;
  sender_name: string | null;
  receiver_name: string | null;
  merchant_name: string | null;
}

export interface LiveAlert {
  id: number;
  customer_id: number;
  customer_name: string | null;
  severity: Severity;
  score: number;
  title: string;
  triggered_rules: string[];
  created_at: string | null;
}

export type WsEvent =
  | { type: "transaction"; data: LiveTransaction }
  | { type: "alert"; data: LiveAlert };

// --- Investigation (graph + timeline) ---

export interface GraphNode {
  id: string;
  kind: "customer" | "merchant";
  label: string;
  sublabel: string | null;
  risk_level: RiskLevel | null;
  is_subject: boolean;
  is_high_risk: boolean;
  total_amount: number;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  amount: number;
  count: number;
  suspicious: boolean;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface TimelineEvent {
  id: string;
  type: "account_opened" | "transaction" | "alert" | "case_opened";
  timestamp: string;
  title: string;
  description: string | null;
  severity: Severity | null;
  amount: number | null;
  flagged: boolean;
}

export interface RiskScore {
  id: number;
  customer_id: number;
  score: number;
  risk_level: RiskLevel;
  breakdown: Array<{
    rule: string;
    name: string;
    points: number;
    reason: string;
    severity: Severity;
    transaction_ids: number[];
  }>;
  computed_at: string;
}

export interface AccountRead {
  id: number;
  customer_id: number;
  account_number: string;
  account_type: string;
  currency: string;
  balance: number;
  opened_at: string;
  last_activity_at: string | null;
  is_dormant: boolean;
}

export interface CustomerDetail extends CustomerSummary {
  annual_income: number;
  expected_monthly_income: number;
  expected_monthly_spend: number;
  date_opened: string;
  accounts: AccountRead[];
  latest_risk: RiskScore | null;
}

export interface CaseRead {
  id: number;
  case_number: string;
  customer_id: number;
  customer_name: string | null;
  alert_id: number | null;
  title: string;
  status: string;
  priority: string;
  ai_summary: Record<string, unknown> | null;
  analyst_notes: string | null;
  opened_at: string;
  closed_at: string | null;
  transaction_count: number;
}

export interface InvestigationBundle {
  customer: CustomerDetail;
  alerts: AlertRead[];
  cases: CaseRead[];
  graph: GraphData;
  timeline: TimelineEvent[];
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

// --- AI summary + SAR (Stage 7) ---

export interface AISummary {
  executive_summary: string;
  key_findings: string[];
  likely_behaviors: string[];
  risk_assessment: string;
  recommended_next_steps: string[];
  generated_by: string;
  model: string | null;
}

export interface SarReportRead {
  id: number;
  case_id: number;
  reference: string;
  summary: string;
  customer_section: string;
  reason: string;
  evidence: unknown[];
  timeline: unknown[];
  recommendation: string;
  analyst_notes: string | null;
  generated_at: string;
}
