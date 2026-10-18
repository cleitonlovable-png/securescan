"use client";

import { useEffect, useState } from "react";
import { Eraser } from "lucide-react";
import Topbar from "@/components/Topbar";
import { ensureSession, getDefaultOrganizationId, listAllScans, ScanHistoryItem } from "@/lib/api";

const STATUS_LABEL: Record<string, string> = {
  PENDING: "Pendente",
  RUNNING: "Em andamento",
  COMPLETED: "Concluído",
  FAILED: "Falhou",
  CANCELLED: "Cancelado",
};

const STATUS_COLOR: Record<string, string> = {
  PENDING: "text-gray-400",
  RUNNING: "text-severity-medium",
  COMPLETED: "text-severity-low",
  FAILED: "text-severity-critical",
  CANCELLED: "text-gray-500",
};

export default function HistoryPage() {
  const [scans, setScans] = useState<ScanHistoryItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cleared, setCleared] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        await ensureSession();
        const orgId = await getDefaultOrganizationId();
        setScans(await listAllScans(orgId));
      } catch (e) {
        setError(e instanceof Error ? e.message : "Erro ao carregar histórico.");
      }
    })();
  }, []);

  return (
    <>
      <Topbar userName="Administrador" userRole="Modo local" />
      <div className="p-8 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-white font-semibold text-lg">Histórico</h2>
            <p className="text-sm text-gray-500">Todas as varreduras já executadas, mais recentes primeiro.</p>
          </div>
          <button
            onClick={() => { setScans([]); setCleared(true); }}
            title="Limpa só o que está na tela — recarregar a página traz o histórico de volta"
            className="flex items-center gap-1.5 text-sm text-gray-400 border border-bg-border hover:border-severity-critical/40 hover:text-severity-critical px-3 py-2 rounded-lg transition-colors"
          >
            <Eraser size={14} /> Limpar tela
          </button>
        </div>

        {error && (
          <div className="rounded-xl border border-severity-critical/40 bg-severity-critical/10 text-severity-critical text-sm px-4 py-3">
            {error}
          </div>
        )}

        <div className="rounded-xl border border-bg-border bg-bg-panel overflow-hidden">
          {scans === null && !error && <div className="p-6 text-sm text-gray-500">Carregando...</div>}

          {scans && scans.length === 0 && cleared && (
            <div className="p-6 text-sm text-gray-500 text-center">
              Tela limpa. Recarregue a página (F5) para ver o histórico de novo.
            </div>
          )}

          {scans && scans.length === 0 && !cleared && (
            <div className="p-6 text-sm text-gray-500 text-center">
              Nenhuma varredura ainda. Inicie a primeira no <a href="/" className="text-brand-red hover:underline">Dashboard</a>.
            </div>
          )}

          {scans && scans.length > 0 && (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b border-bg-border">
                  <th className="px-5 py-3 font-medium">Alvo</th>
                  <th className="px-5 py-3 font-medium">Tipo</th>
                  <th className="px-5 py-3 font-medium">Status</th>
                  <th className="px-5 py-3 font-medium">Achados</th>
                  <th className="px-5 py-3 font-medium">Data</th>
                </tr>
              </thead>
              <tbody>
                {scans.map((s) => (
                  <tr key={s.id} className="border-b border-bg-border last:border-0 hover:bg-bg-panelHover">
                    <td className="px-5 py-3 text-gray-200">{s.domain_hostname}</td>
                    <td className="px-5 py-3 text-gray-400">{s.scan_type}</td>
                    <td className={`px-5 py-3 font-medium ${STATUS_COLOR[s.status] || "text-gray-400"}`}>
                      {STATUS_LABEL[s.status] || s.status}
                    </td>
                    <td className="px-5 py-3 text-gray-400">{s.total_findings}</td>
                    <td className="px-5 py-3 text-gray-500">
                      {new Date(s.created_at).toLocaleString("pt-BR")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </>
  );
}
