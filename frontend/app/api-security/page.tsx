"use client";

import { useEffect, useRef, useState } from "react";
import { Cloud } from "lucide-react";
import Topbar from "@/components/Topbar";
import ScanProgressPanel, { ScanStep } from "@/components/ScanProgressPanel";
import FindingsList from "@/components/FindingsList";
import ScanResultHeader from "@/components/ScanResultHeader";
import WebhookStatusBanner from "@/components/WebhookStatusBanner";
import {
  ensureSession, getDefaultOrganizationId, startApiSecurityScan,
  getScanStatus, getScanFindings, getScanDiff, ScanDiff,
} from "@/lib/api";

const API_SCAN_STEP_LABELS = [
  "Testando controle de acesso (IDOR)",
  "Verificando especificação da API",
  "Testando proteção contra brute-force",
  "Gerando relatório",
];

type FindingItem = Awaited<ReturnType<typeof getScanFindings>>[number];

export default function ApiSecurityPage() {
  const [orgId, setOrgId] = useState<string | null>(null);
  const [initError, setInitError] = useState<string | null>(null);

  const [appUrl, setAppUrl] = useState("");
  const [openapiUrl, setOpenapiUrl] = useState("");
  const [graphqlUrl, setGraphqlUrl] = useState("");
  const [idorSampleUrl, setIdorSampleUrl] = useState("");
  const [idorCookie, setIdorCookie] = useState("");
  const [rateLimitTestUrl, setRateLimitTestUrl] = useState("");
  const [authorized, setAuthorized] = useState(false);

  const [scanning, setScanning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState<string | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [findings, setFindings] = useState<FindingItem[] | null>(null);
  const [scanDiff, setScanDiff] = useState<ScanDiff | null>(null);
  const [webhookStatus, setWebhookStatus] = useState<"sent" | "failed" | null>(null);
  const [webhookError, setWebhookError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const activeScanRef = useRef<{ projectId: string; scanId: string } | null>(null);
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const elapsedTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    (async () => {
      try {
        await ensureSession();
        setOrgId(await getDefaultOrganizationId());
      } catch (e) {
        setInitError(e instanceof Error ? e.message : "Erro ao conectar com o backend.");
      }
    })();
    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
      if (elapsedTimerRef.current) clearInterval(elapsedTimerRef.current);
    };
  }, []);

  function stopTimers() {
    if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    if (elapsedTimerRef.current) clearInterval(elapsedTimerRef.current);
  }

  async function handleStart() {
    setFormError(null);
    if (!orgId) return;
    if (!appUrl.trim()) { setFormError("Informe a URL da API/app."); return; }
    if (!openapiUrl.trim() && !graphqlUrl.trim() && !idorSampleUrl.trim() && !rateLimitTestUrl.trim()) {
      setFormError("Informe ao menos um: URL do OpenAPI, do GraphQL, de exemplo para IDOR, ou de rate limiting.");
      return;
    }
    if (!authorized) { setFormError("Confirme que você tem autorização para testar este alvo."); return; }

    setScanning(true);
    setFindings(null);
    setScanDiff(null);
    setWebhookStatus(null);
    setWebhookError(null);
    setProgress(0);
    setCurrentStep("Iniciando...");
    setElapsedSeconds(0);

    try {
      const scan = await startApiSecurityScan(orgId, appUrl.trim(), {
        openapiUrl: openapiUrl.trim(),
        graphqlUrl: graphqlUrl.trim(),
        idorSampleUrl: idorSampleUrl.trim(),
        idorSessionCookie: idorCookie.trim(),
        rateLimitTestUrl: rateLimitTestUrl.trim(),
      });
      activeScanRef.current = { projectId: scan.project_id, scanId: scan.id };

      elapsedTimerRef.current = setInterval(() => setElapsedSeconds((s) => s + 1), 1000);

      pollTimerRef.current = setInterval(async () => {
        if (!activeScanRef.current) return;
        const { projectId, scanId } = activeScanRef.current;
        try {
          const status = await getScanStatus(orgId, projectId, scanId);
          setProgress(status.progress_percent);
          setCurrentStep(status.current_step);

          if (status.status === "COMPLETED" || status.status === "FAILED" || status.status === "CANCELLED") {
            stopTimers();
            if (status.status === "COMPLETED") {
              const result = await getScanFindings(orgId, projectId, scanId);
              setFindings(result);
              setScanDiff(await getScanDiff(orgId, projectId, scanId));
              setWebhookStatus(status.webhook_status);
              setWebhookError(status.webhook_error);
            }
            setScanning(false);
          }
        } catch {
          stopTimers();
          setCurrentStep("Erro ao consultar o andamento do scan.");
          setScanning(false);
        }
      }, 1500);
    } catch (e) {
      setScanning(false);
      setFormError(e instanceof Error ? e.message : "Erro ao iniciar a verificação.");
    }
  }

  function handleCancel() {
    stopTimers();
    setScanning(false);
    activeScanRef.current = null;
  }

  const currentStepIndex = currentStep ? API_SCAN_STEP_LABELS.indexOf(currentStep) : -1;
  const steps: ScanStep[] = API_SCAN_STEP_LABELS.map((label, i) => ({
    label,
    done: currentStepIndex === -1 ? false : i < currentStepIndex || progress === 100,
  }));

  function formatElapsed(totalSeconds: number): string {
    const m = Math.floor(totalSeconds / 60).toString().padStart(2, "0");
    const s = (totalSeconds % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
  }

  return (
    <>
      <Topbar userName="Administrador" userRole="Modo local" />
      <div className="p-8 space-y-6">
        {initError && (
          <div className="rounded-xl border border-severity-critical/40 bg-severity-critical/10 text-severity-critical text-sm px-4 py-3">
            {initError}
          </div>
        )}

        <div className="rounded-xl border border-bg-border bg-bg-panel p-6">
          <div className="flex items-center gap-3 mb-1">
            <div className="w-10 h-10 rounded-lg bg-brand-red/15 text-brand-red flex items-center justify-center">
              <Cloud size={20} />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">Segurança de API</h2>
              <p className="text-sm text-gray-500">
                Endpoints sem autenticação, exposição de dados na resposta, introspecção GraphQL
                habilitada, e controle de acesso entre registros (IDOR).
              </p>
            </div>
          </div>

          {formError && (
            <div className="mt-4 text-sm text-severity-critical bg-severity-critical/10 border border-severity-critical/30 rounded-lg px-3 py-2">
              {formError}
            </div>
          )}

          <div className="mt-4 space-y-3">
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">URL da API/app (para organizar o projeto)</label>
              <input
                value={appUrl} onChange={(e) => setAppUrl(e.target.value)}
                placeholder="https://api.seudominio.com"
                className="w-full bg-bg border border-bg-border rounded-lg px-4 py-2.5 text-sm text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-brand-red/50"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">URL da especificação OpenAPI/Swagger (opcional)</label>
              <input
                value={openapiUrl} onChange={(e) => setOpenapiUrl(e.target.value)}
                placeholder="https://api.seudominio.com/openapi.json"
                className="w-full bg-bg border border-bg-border rounded-lg px-4 py-2.5 text-sm text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-brand-red/50"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">URL do endpoint GraphQL (opcional)</label>
              <input
                value={graphqlUrl} onChange={(e) => setGraphqlUrl(e.target.value)}
                placeholder="https://api.seudominio.com/graphql"
                className="w-full bg-bg border border-bg-border rounded-lg px-4 py-2.5 text-sm text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-brand-red/50"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1">URL de exemplo com ID (IDOR, opcional)</label>
                <input
                  value={idorSampleUrl} onChange={(e) => setIdorSampleUrl(e.target.value)}
                  placeholder="https://api.../pedido/145"
                  className="w-full bg-bg border border-bg-border rounded-lg px-4 py-2.5 text-sm text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-brand-red/50"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1">Cookie de sessão (opcional)</label>
                <input
                  value={idorCookie} onChange={(e) => setIdorCookie(e.target.value)}
                  placeholder="session=abc123"
                  className="w-full bg-bg border border-bg-border rounded-lg px-4 py-2.5 text-sm text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-brand-red/50"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">
                URL para testar rate limiting (opcional — ex: endpoint de login)
              </label>
              <input
                value={rateLimitTestUrl} onChange={(e) => setRateLimitTestUrl(e.target.value)}
                placeholder="https://api.../auth/login"
                className="w-full bg-bg border border-bg-border rounded-lg px-4 py-2.5 text-sm text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-brand-red/50"
              />
              <p className="text-[11px] text-gray-600 mt-1">
                Manda até 15 requisições seguidas (nunca mais que isso) pra ver se o endpoint bloqueia — não é um brute-force de verdade.
              </p>
            </div>

            <label className="flex items-start gap-2 text-sm text-gray-300 cursor-pointer">
              <input type="checkbox" checked={authorized} onChange={(e) => setAuthorized(e.target.checked)} className="accent-brand-red w-4 h-4 mt-0.5" />
              Confirmo que esta API é minha ou tenho autorização para testá-la
            </label>

            <button
              onClick={handleStart} disabled={scanning}
              className="w-full bg-brand-red hover:bg-brand-red/90 disabled:opacity-50 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition-colors"
            >
              {scanning ? "Verificando..." : "Verificar Segurança de API →"}
            </button>
          </div>
        </div>

        {scanning && (
          <ScanProgressPanel percent={progress} steps={steps} elapsed={formatElapsed(elapsedSeconds)} onCancel={handleCancel} />
        )}

        {findings && (
          <>
            <ScanResultHeader
              diff={scanDiff}
              organizationId={orgId}
              projectId={activeScanRef.current?.projectId ?? null}
              scanId={activeScanRef.current?.scanId ?? null}
            />
            <WebhookStatusBanner status={webhookStatus} error={webhookError} />
            <FindingsList findings={findings} />
          </>
        )}
      </div>
    </>
  );
}
