"use client";

import { useEffect, useRef, useState } from "react";
import { Lock } from "lucide-react";
import Topbar from "@/components/Topbar";
import SeverityCard from "@/components/SeverityCard";
import NewScanPanel from "@/components/NewScanPanel";
import ScanProgressPanel, { ScanStep } from "@/components/ScanProgressPanel";
import RecentScansList from "@/components/RecentScansList";
import ModuleGrid from "@/components/ModuleGrid";
import FindingsList from "@/components/FindingsList";
import ScanResultHeader from "@/components/ScanResultHeader";
import WebhookStatusBanner from "@/components/WebhookStatusBanner";
import {
  ensureSession, getDefaultOrganizationId, startQuickScan,
  getScanStatus, getScanFindings, getDashboard, getScanDiff, ScanDiff,
} from "@/lib/api";
import type { DashboardData } from "@/lib/types";

// Mesma ordem definida em scanner-engine/registry.py::plugins_for_scan_type("FULL_SCAN")
const FULL_SCAN_STEP_LABELS = [
  "Verificando headers de segurança",
  "Verificando certificado SSL/TLS",
  "Identificando tecnologias utilizadas",
  "Escaneando portas abertas",
  "Verificando arquivos sensíveis expostos",
  "Buscando chaves e segredos vazados",
  "Verificando exposição de banco de dados",
  "Verificando exposição de dados pessoais (LGPD)",
  "Verificando dependências vulneráveis",
  "Gerando relatório",
];

type FindingItem = Awaited<ReturnType<typeof getScanFindings>>[number];

export default function DashboardPage() {
  const [orgId, setOrgId] = useState<string | null>(null);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [scanning, setScanning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState<string | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [findings, setFindings] = useState<FindingItem[] | null>(null);
  const [scanDiff, setScanDiff] = useState<ScanDiff | null>(null);
  const [historyCleared, setHistoryCleared] = useState(false);
  const [webhookStatus, setWebhookStatus] = useState<"sent" | "failed" | null>(null);
  const [webhookError, setWebhookError] = useState<string | null>(null);

  const activeScanRef = useRef<{ projectId: string; scanId: string } | null>(null);
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const elapsedTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  async function refreshDashboard(currentOrgId: string) {
    try {
      setDashboard(await getDashboard(currentOrgId));
      setHistoryCleared(false);
    } catch {
      // silencioso — dashboard vazio ainda é um estado válido logo após o bootstrap
    }
  }

  useEffect(() => {
    (async () => {
      try {
        await ensureSession();
        const id = await getDefaultOrganizationId();
        setOrgId(id);
        await refreshDashboard(id);
      } catch (e) {
        setLoadError(e instanceof Error ? e.message : "Erro ao conectar com o backend.");
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

  async function handleStartScan(url: string) {
    if (!orgId || !url.trim()) return;

    setScanning(true);
    setFindings(null);
    setScanDiff(null);
    setWebhookStatus(null);
    setWebhookError(null);
    setProgress(0);
    setCurrentStep("Iniciando...");
    setElapsedSeconds(0);

    try {
      const scan = await startQuickScan(orgId, url.trim());
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
            await refreshDashboard(orgId);
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
      setCurrentStep(null);
      setLoadError(e instanceof Error ? e.message : "Erro ao iniciar a varredura.");
    }
  }

  function handleCancel() {
    stopTimers();
    setScanning(false);
    activeScanRef.current = null;
  }

  const summary = dashboard?.severity_summary ?? { critical: 0, high: 0, medium: 0, low: 0, info: 0 };
  const recentScans = historyCleared ? [] : (dashboard?.recent_scans ?? []);

  const currentStepIndex = currentStep ? FULL_SCAN_STEP_LABELS.indexOf(currentStep) : -1;
  const steps: ScanStep[] = FULL_SCAN_STEP_LABELS.map((label, i) => ({
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
        {loadError && (
          <div className="rounded-xl border border-severity-critical/40 bg-severity-critical/10 text-severity-critical text-sm px-4 py-3">
            {loadError}
          </div>
        )}

        <NewScanPanel onStartScan={handleStartScan} />

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <SeverityCard variant="critical" label="Vulnerabilidades Críticas" count={summary.critical} description="Requerem ação imediata" />
          <SeverityCard variant="high" label="Vulnerabilidades Altas" count={summary.high} description="Alto risco para o sistema" />
          <SeverityCard variant="medium" label="Vulnerabilidades Médias" count={summary.medium} description="Correção recomendada" />
          <SeverityCard variant="low" label="Informações / Baixo" count={summary.low} description="Boas práticas" />
        </div>

        {scanning && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <ScanProgressPanel
              percent={progress}
              steps={steps}
              elapsed={formatElapsed(elapsedSeconds)}
              onCancel={handleCancel}
            />
            <RecentScansList scans={recentScans} cleared={historyCleared} onClear={() => setHistoryCleared(true)} />
          </div>
        )}

        {!scanning && <RecentScansList scans={recentScans} cleared={historyCleared} onClear={() => setHistoryCleared(true)} />}

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

        <ModuleGrid />

        <div className="rounded-xl border border-brand-red/30 bg-brand-red/10 p-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Lock className="text-brand-red" size={24} />
            <div>
              <div className="text-white font-semibold">Segurança não é um gasto, é um investimento.</div>
              <div className="text-sm text-gray-400">Proteja seus dados, seus clientes e o futuro do seu negócio.</div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
