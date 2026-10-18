"use client";

import { FileDown, FileText, FileSpreadsheet, Presentation } from "lucide-react";
import { downloadScanReport, downloadScanReportHtml, downloadScanReportCsv, downloadExecutiveReport, ScanDiff } from "@/lib/api";

interface ScanResultHeaderProps {
  diff: ScanDiff | null;
  organizationId: string | null;
  projectId: string | null;
  scanId: string | null;
}

export default function ScanResultHeader({ diff, organizationId, projectId, scanId }: ScanResultHeaderProps) {
  const canDownload = !!(organizationId && projectId && scanId);

  function handle(fn: (org: string, proj: string, scan: string) => Promise<void>) {
    if (organizationId && projectId && scanId) fn(organizationId, projectId, scanId);
  }

  return (
    <div className="rounded-xl border border-bg-border bg-bg-panel p-4 flex items-center justify-between gap-4 flex-wrap">
      <div className="text-sm">
        {!diff || !diff.has_previous_scan ? (
          <span className="text-gray-500">🆕 Primeira varredura registrada para este alvo.</span>
        ) : diff.new_count === 0 && diff.resolved_count === 0 ? (
          <span className="text-gray-500">✅ Nenhuma mudança desde a última varredura.</span>
        ) : (
          <span className="text-gray-300">
            {diff.new_count > 0 && (
              <span className="text-severity-critical font-medium">🔺 {diff.new_count} achado(s) novo(s)</span>
            )}
            {diff.new_count > 0 && diff.resolved_count > 0 && " · "}
            {diff.resolved_count > 0 && (
              <span className="text-severity-low font-medium">✅ {diff.resolved_count} corrigido(s)</span>
            )}
            {" "}desde a última varredura
          </span>
        )}
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => handle(downloadExecutiveReport)}
          disabled={!canDownload}
          title="Resumo enxuto para quem não é técnico"
          className="flex items-center gap-2 text-sm text-gray-200 border border-severity-medium/40 hover:border-severity-medium hover:text-severity-medium disabled:opacity-40 px-3 py-2 rounded-lg transition-colors"
        >
          <Presentation size={16} /> Resumo Executivo
        </button>
        <button
          onClick={() => handle(downloadScanReport)}
          disabled={!canDownload}
          className="flex items-center gap-2 text-sm text-gray-200 border border-bg-border hover:border-brand-red/40 hover:text-brand-red disabled:opacity-40 px-3 py-2 rounded-lg transition-colors"
        >
          <FileDown size={16} /> PDF
        </button>
        <button
          onClick={() => handle(downloadScanReportHtml)}
          disabled={!canDownload}
          className="flex items-center gap-2 text-sm text-gray-200 border border-bg-border hover:border-brand-red/40 hover:text-brand-red disabled:opacity-40 px-3 py-2 rounded-lg transition-colors"
        >
          <FileText size={16} /> HTML
        </button>
        <button
          onClick={() => handle(downloadScanReportCsv)}
          disabled={!canDownload}
          className="flex items-center gap-2 text-sm text-gray-200 border border-bg-border hover:border-brand-red/40 hover:text-brand-red disabled:opacity-40 px-3 py-2 rounded-lg transition-colors"
        >
          <FileSpreadsheet size={16} /> CSV
        </button>
      </div>
    </div>
  );
}
