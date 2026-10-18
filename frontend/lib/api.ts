// "" (string vazia) é um valor válido e proposital no build desktop — significa
// "mesma origem" (API e frontend servidos pela mesma porta). Só cai no
// localhost:8000 quando a variável nem foi definida (undefined), como no
// modo Docker/dev.
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("securescan_access_token");
}

async function refreshSession(): Promise<void> {
  const res = await fetch(`${API_URL}/api/v1/auth/dev-bootstrap`, { method: "POST" });
  if (!res.ok) throw new Error("Não foi possível renovar a sessão.");
  const data = await res.json();
  localStorage.setItem("securescan_access_token", data.access_token);
}

async function request<T>(path: string, options: RequestInit = {}, _isRetry = false): Promise<T> {
  const token = getToken();

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  // sessão expirada (padrão em uso prolongado): renova sozinho e tenta de novo,
  // uma única vez, sem incomodar o usuário com esse erro
  if (res.status === 401 && !_isRetry) {
    await refreshSession();
    return request<T>(path, options, true);
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Erro na requisição: ${res.status}`);
  }

  return res.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, data?: unknown) =>
    request<T>(path, { method: "POST", body: data ? JSON.stringify(data) : undefined }),
  put: <T>(path: string, data?: unknown) =>
    request<T>(path, { method: "PUT", body: data ? JSON.stringify(data) : undefined }),
  patch: <T>(path: string, data?: unknown) =>
    request<T>(path, { method: "PATCH", body: data ? JSON.stringify(data) : undefined }),
};

export async function login(email: string, password: string) {
  const form = new URLSearchParams();
  form.set("username", email);
  form.set("password", password);

  const res = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form.toString(),
  });

  if (!res.ok) throw new Error("E-mail ou senha inválidos.");

  const data = await res.json();
  localStorage.setItem("securescan_access_token", data.access_token);
  return data;
}

export async function registerUser(
  email: string, password: string, fullName: string, organizationName: string,
): Promise<void> {
  const res = await fetch(`${API_URL}/api/v1/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email, password, full_name: fullName, organization_name: organizationName,
    }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || "Não foi possível criar a conta.");
  }

  // registro não retorna token — loga em seguida com as mesmas credenciais
  await login(email, password);
}

/**
 * Modo local (Fase 43): garante que existe uma sessão válida sem exigir
 * tela de cadastro ainda. Ver backend/app/api/v1/auth.py::dev_bootstrap.
 */
export async function ensureSession(): Promise<void> {
  if (getToken()) return;
  await refreshSession();
}

export async function getDefaultOrganizationId(): Promise<string> {
  const cached = typeof window !== "undefined" ? localStorage.getItem("securescan_org_id") : null;
  if (cached) return cached;

  const orgs = await api.get<{ id: string; name: string }[]>("/api/v1/organizations");
  if (orgs.length === 0) throw new Error("Nenhuma organização encontrada para este usuário.");

  localStorage.setItem("securescan_org_id", orgs[0].id);
  return orgs[0].id;
}

export interface QuickScanResult {
  id: string;
  project_id: string;
  domain_id: string;
  status: string;
}

export function startQuickScan(organizationId: string, url: string) {
  return api.post<QuickScanResult>(`/api/v1/organizations/${organizationId}/quick-scan`, {
    url,
    scan_type: "FULL_SCAN",
    authorize: true,
  });
}

export function startPentestScan(organizationId: string, url: string, zapApiKey: string) {
  return api.post<QuickScanResult>(`/api/v1/organizations/${organizationId}/quick-scan`, {
    url,
    scan_type: "PENTEST_SCAN",
    authorize: true,
    zap_api_key: zapApiKey,
  });
}

export function startCodeScan(organizationId: string, url: string, repoUrl: string, repoBranch?: string) {
  return api.post<QuickScanResult>(`/api/v1/organizations/${organizationId}/quick-scan`, {
    url,
    scan_type: "CODE_SCAN",
    authorize: true,
    repo_url: repoUrl,
    repo_branch: repoBranch || undefined,
  });
}

export function startApiSecurityScan(
  organizationId: string, url: string,
  options: { openapiUrl?: string; graphqlUrl?: string; idorSampleUrl?: string; idorSessionCookie?: string; rateLimitTestUrl?: string },
) {
  return api.post<QuickScanResult>(`/api/v1/organizations/${organizationId}/quick-scan`, {
    url,
    scan_type: "API_SCAN",
    authorize: true,
    openapi_url: options.openapiUrl || undefined,
    graphql_url: options.graphqlUrl || undefined,
    idor_sample_url: options.idorSampleUrl || undefined,
    idor_session_cookie: options.idorSessionCookie || undefined,
    rate_limit_test_url: options.rateLimitTestUrl || undefined,
  });
}

export function startInfraScan(
  organizationId: string, url: string,
  options: { dockerfileContent?: string; bucketUrl?: string },
) {
  return api.post<QuickScanResult>(`/api/v1/organizations/${organizationId}/quick-scan`, {
    url,
    scan_type: "INFRA_SCAN",
    authorize: true,
    dockerfile_content: options.dockerfileContent || undefined,
    bucket_url: options.bucketUrl || undefined,
  });
}

export function startSupabaseScan(organizationId: string, url: string, supabaseUrl: string, supabaseAnonKey: string) {
  return api.post<QuickScanResult>(`/api/v1/organizations/${organizationId}/quick-scan`, {
    url,
    scan_type: "SUPABASE_SCAN",
    authorize: true,
    supabase_url: supabaseUrl,
    supabase_anon_key: supabaseAnonKey,
  });
}

export function startCheckoutScan(organizationId: string, checkoutUrl: string) {
  return api.post<QuickScanResult>(`/api/v1/organizations/${organizationId}/quick-scan`, {
    url: checkoutUrl,
    scan_type: "CHECKOUT_SCAN",
    authorize: true,
  });
}

export function getScanStatus(organizationId: string, projectId: string, scanId: string) {
  return api.get<{
    id: string;
    status: string;
    progress_percent: number;
    current_step: string | null;
    severity_summary: { critical: number; high: number; medium: number; low: number; info: number };
    webhook_status: "sent" | "failed" | null;
    webhook_error: string | null;
  }>(`/api/v1/organizations/${organizationId}/projects/${projectId}/scans/${scanId}`);
}

export function getScanFindings(organizationId: string, projectId: string, scanId: string) {
  return api.get<
    { id: string; title: string; description: string; severity: string; remediation: string | null; endpoint_or_file: string | null }[]
  >(`/api/v1/organizations/${organizationId}/projects/${projectId}/scans/${scanId}/findings`);
}

export function getDashboard(organizationId: string) {
  return api.get<import("./types").DashboardData>(`/api/v1/organizations/${organizationId}/dashboard`);
}

export interface VulnerabilityItem {
  id: string;
  title: string;
  description: string;
  severity: string;
  remediation: string | null;
  endpoint_or_file: string | null;
  category: string;
  project_name: string;
  domain_hostname: string;
  created_at: string;
}

export function listVulnerabilities(organizationId: string, category?: string) {
  const query = category ? `?category=${encodeURIComponent(category)}` : "";
  return api.get<VulnerabilityItem[]>(`/api/v1/organizations/${organizationId}/vulnerabilities${query}`);
}

export interface ScanHistoryItem {
  id: string;
  project_name: string;
  domain_hostname: string;
  scan_type: string;
  status: string;
  total_findings: number;
  created_at: string;
  finished_at: string | null;
}

export function listAllScans(organizationId: string) {
  return api.get<ScanHistoryItem[]>(`/api/v1/organizations/${organizationId}/scans`);
}

export interface ProjectItem {
  id: string;
  name: string;
  description: string | null;
  environment: string;
  security_score: number | null;
  last_scan_at: string | null;
}

export function listProjects(organizationId: string) {
  return api.get<ProjectItem[]>(`/api/v1/organizations/${organizationId}/projects`);
}

export interface WebhookSettings {
  webhook_url: string | null;
  webhook_secret: string | null;
  slack_webhook_url: string | null;
}

export function getWebhookSettings(organizationId: string) {
  return api.get<WebhookSettings>(`/api/v1/organizations/${organizationId}/webhook`);
}

export function updateWebhookSettings(organizationId: string, settings: WebhookSettings) {
  return api.put<WebhookSettings>(`/api/v1/organizations/${organizationId}/webhook`, settings);
}

export function generateWebhookSecret(organizationId: string) {
  return api.post<WebhookSettings>(`/api/v1/organizations/${organizationId}/webhook/generate-secret`);
}

export interface OrganizationItem {
  id: string;
  name: string;
  plan: string;
}

export function listOrganizations() {
  return api.get<OrganizationItem[]>("/api/v1/organizations");
}

export function createOrganization(name: string) {
  return api.post<OrganizationItem>("/api/v1/organizations", { name });
}

export interface MemberItem {
  id: string;
  user_id: string;
  email: string;
  full_name: string;
  role: "OWNER" | "ADMIN" | "SECURITY_ANALYST" | "DEVELOPER" | "VIEWER";
}

export function listMembers(organizationId: string) {
  return api.get<MemberItem[]>(`/api/v1/organizations/${organizationId}/members`);
}

export function inviteMember(organizationId: string, email: string, role: string) {
  return api.post<MemberItem>(`/api/v1/organizations/${organizationId}/members`, { email, role });
}

export async function removeMember(organizationId: string, membershipId: string): Promise<void> {
  const token = getToken();
  const res = await fetch(`${API_URL}/api/v1/organizations/${organizationId}/members/${membershipId}`, {
    method: "DELETE",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || "Não foi possível remover o membro.");
  }
}

export function setActiveOrganization(organizationId: string): void {
  localStorage.setItem("securescan_org_id", organizationId);
}

export interface ScanDiff {
  has_previous_scan: boolean;
  new_count: number;
  resolved_count: number;
  new_findings: string[];
  resolved_findings: string[];
}

export function getScanDiff(organizationId: string, projectId: string, scanId: string) {
  return api.get<ScanDiff>(`/api/v1/organizations/${organizationId}/projects/${projectId}/scans/${scanId}/diff`);
}

export async function downloadScanReport(organizationId: string, projectId: string, scanId: string): Promise<void> {
  await downloadFile(
    `/api/v1/organizations/${organizationId}/projects/${projectId}/scans/${scanId}/report.pdf`,
    `relatorio_${scanId}.pdf`,
  );
}

export async function downloadScanReportHtml(organizationId: string, projectId: string, scanId: string): Promise<void> {
  await downloadFile(
    `/api/v1/organizations/${organizationId}/projects/${projectId}/scans/${scanId}/report.html`,
    `relatorio_${scanId}.html`,
  );
}

export async function downloadScanReportCsv(organizationId: string, projectId: string, scanId: string): Promise<void> {
  await downloadFile(
    `/api/v1/organizations/${organizationId}/projects/${projectId}/scans/${scanId}/report.csv`,
    `relatorio_${scanId}.csv`,
  );
}

export async function downloadExecutiveReport(organizationId: string, projectId: string, scanId: string): Promise<void> {
  await downloadFile(
    `/api/v1/organizations/${organizationId}/projects/${projectId}/scans/${scanId}/report/executive.pdf`,
    `resumo_executivo_${scanId}.pdf`,
  );
}

async function downloadFile(path: string, filename: string): Promise<void> {
  const token = getToken();
  const res = await fetch(`${API_URL}${path}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
  if (!res.ok) throw new Error("Não foi possível gerar o arquivo.");

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export interface UpdateCheckResponse {
  current_version: string;
  latest_version: string;
  update_available: boolean;
  notes: string;
  download_url: string;
}

export function checkSystemUpdate() {
  return api.get<UpdateCheckResponse>("/api/v1/system/update-check");
}

export function applySystemUpdate() {
  return api.post<{ status: string; message: string }>("/api/v1/system/update-apply");
}

