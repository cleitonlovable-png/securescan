export type Severity = "critical" | "high" | "medium" | "low" | "info";

export type ScanType =
  | "QUICK_SCAN"
  | "FULL_SCAN"
  | "API_SCAN"
  | "INFRA_SCAN"
  | "CHECKOUT_SCAN";

export type ScanStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED" | "CANCELLED";

export interface SeveritySummary {
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
}

export interface RecentScanItem {
  id: string;
  project_name: string;
  domain_hostname: string;
  status: ScanStatus;
  total_findings: number;
  highest_severity: Severity | null;
  finished_at: string | null;
}

export interface DashboardData {
  security_score: number | null;
  severity_summary: SeveritySummary;
  total_projects: number;
  recent_scans: RecentScanItem[];
}

export interface Project {
  id: string;
  name: string;
  description: string | null;
  environment: "production" | "staging" | "development";
  framework: string | null;
  security_score: number | null;
  last_scan_at: string | null;
  created_at: string;
}

export interface Domain {
  id: string;
  hostname: string;
  verification_status: "PENDING_VERIFICATION" | "VERIFIED" | "FAILED" | "PRIVATE_ENVIRONMENT";
  verification_token: string;
}

export interface ScanWithSummary {
  id: string;
  project_id: string;
  domain_id: string;
  scan_type: ScanType;
  status: ScanStatus;
  progress_percent: number;
  current_step: string | null;
  severity_summary: SeveritySummary;
}

export interface Finding {
  id: string;
  scan_id: string;
  plugin_name: string;
  title: string;
  description: string;
  category: string;
  severity: Severity;
  confidence: "high" | "medium" | "low";
  cwe: string | null;
  owasp: string | null;
  endpoint_or_file: string | null;
  evidence_sanitized: string | null;
  remediation: string | null;
  references: string[];
  status: string;
  created_at: string;
}
