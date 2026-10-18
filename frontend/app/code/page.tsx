"use client";

import { useEffect, useRef, useState } from "react";
import { Code2, GitBranch } from "lucide-react";
import Topbar from "@/components/Topbar";
import ScanProgressPanel, { ScanStep } from "@/components/ScanProgressPanel";
import FindingsList from "@/components/FindingsList";
import ScanResultHeader from "@/components/ScanResultHeader";
import WebhookStatusBanner from "@/components/WebhookStatusBanner";
import {
  ensureSession, getDefaultOrganizationId, startCodeScan,
  getScanStatus, getScanFindings, getScanDiff, ScanDiff,
} from "@/lib/api";

const CODE_SCAN_STEP_LABELS = [
  "Clonando repositório e analisando o código",
  "Gerando relatório",
];

type FindingItem = Awaited<ReturnType<typeof getScanFindings>>[number];

export default function CodePage() {
  const [orgId, setOrgId] = useState<string | null>(null);
  const [initError, setInitError] = useState<string | null>(null);

  const [appUrl, setAppUrl] = useState("");
  const [repoUrl, setRepoUrl] = useState("");
  const [branch, setBranch] = useState("");
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
    if (!appUrl.trim()) { setFormError("Informe a URL do app (usada para organizar o projeto)."); return; }
    if (!repoUrl.trim()) { setFormError("Informe a URL do repositório Git."); return; }
    if (!authorized) { setFormError("Confirme que você tem autorização para analisar este código."); return; }

    setScanning(true);
    setFindings(null);
    setScanDiff(null);
    setWebhookStatus(null);
    setWebhookError(null);
    setProgress(0);
    setCurrentStep("Iniciando...");
    setElapsedSeconds(0);

    try {
      const scan = await startCodeScan(orgId, appUrl.trim(), repoUrl.trim(), branch.trim() || undefined);
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
      setFormError(e instanceof Error ? e.message : "Erro ao iniciar a análise.");
    }
  }

  function handleCancel() {
    stopTimers();
    setScanning(false);
    activeScanRef.current = null;
  }

  const currentStepIndex = currentStep ? CODE_SCAN_STEP_LABELS.indexOf(currentStep) : -1;
  const steps: ScanStep[] = CODE_SCAN_STEP_LABELS.map((label, i) => ({
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
              <Code2 size={20} />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">Análise de Código</h2>
              <p className="text-sm text-gray-500">
                Clona seu repositório e roda o Semgrep: SQL Injection por concatenação, comandos
                perigosos (eval/exec), criptografia insegura, e mais.
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
              <label className="block text-xs font-medium text-gray-400 mb-1">URL do app (para organizar o projeto)</label>
              <input
                value={appUrl} onChange={(e) => setAppUrl(e.target.value)}
                placeholder="https://seudominio.com"
                className="w-full bg-bg border border-bg-border rounded-lg px-4 py-2.5 text-sm text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-brand-red/50"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1 flex items-center gap-1.5">
                <GitBranch size={12} /> URL do repositório Git
              </label>
              <input
                value={repoUrl} onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://github.com/seu-usuario/seu-repo.git"
                className="w-full bg-bg border border-bg-border rounded-lg px-4 py-2.5 text-sm text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-brand-red/50"
              />
              <p className="text-[11px] text-gray-600 mt-1">
                Repositório privado? Cole a URL já com o token: https://SEU_TOKEN@github.com/...
              </p>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">Branch (opcional)</label>
              <input
                value={branch} onChange={(e) => setBranch(e.target.value)}
                placeholder="main"
                className="w-full bg-bg border border-bg-border rounded-lg px-4 py-2.5 text-sm text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-brand-red/50"
              />
            </div>

            <label className="flex items-start gap-2 text-sm text-gray-300 cursor-pointer">
              <input type="checkbox" checked={authorized} onChange={(e) => setAuthorized(e.target.checked)} className="accent-brand-red w-4 h-4 mt-0.5" />
              Confirmo que este código é meu ou tenho autorização para analisá-lo
            </label>

            <button
              onClick={handleStart} disabled={scanning}
              className="w-full bg-brand-red hover:bg-brand-red/90 disabled:opacity-50 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition-colors"
            >
              {scanning ? "Analisando..." : "Iniciar Análise de Código →"}
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
