"use client";

import { ShieldAlert, ShieldCheck, Database, Shield, Eraser } from "lucide-react";
import Link from "next/link";
import type { RecentScanItem } from "@/lib/types";

const SEVERITY_BADGE: Record<string, string> = {
  critical: "bg-severity-critical/15 text-severity-critical",
  high: "bg-severity-high/15 text-severity-high",
  medium: "bg-severity-medium/15 text-severity-medium",
  low: "bg-severity-low/15 text-severity-low",
};

function iconFor(item: RecentScanItem) {
  if (!item.highest_severity) return ShieldCheck;
  if (item.highest_severity === "critical") return ShieldAlert;
  return Shield;
}

function formatDate(iso: string | null): string {
  if (!iso) return "Em andamento";
  const d = new Date(iso);
  return d.toLocaleDateString("pt-BR") + " " + d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}

interface RecentScansListProps {
  scans: RecentScanItem[];
  onClear?: () => void;
  cleared?: boolean;
}

export default function RecentScansList({ scans, onClear, cleared = false }: RecentScansListProps) {
  return (
    <div className="rounded-xl border border-bg-border bg-bg-panel p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-white font-semibold">Últimas Varreduras</h3>
        <div className="flex items-center gap-3">
          {onClear && (
            <button
              onClick={onClear}
              title="Limpa só o que está na tela — recarregar a página traz o histórico de volta"
              className="flex items-center gap-1 text-xs text-gray-400 hover:text-severity-critical transition-colors"
            >
              <Eraser size={12} /> Limpar tela
            </button>
          )}
          <Link href="/history" className="text-xs text-brand-red hover:underline">Ver todas →</Link>
        </div>
      </div>

      <ul className="space-y-3">
        {scans.length === 0 && cleared && (
          <li className="text-sm text-gray-500">Tela limpa. Recarregue a página (F5) para ver o histórico de novo.</li>
        )}
        {scans.length === 0 && !cleared && (
          <li className="text-sm text-gray-500">Nenhuma varredura ainda. Inicie a primeira acima.</li>
        )}
        {scans.map((scan) => {
          const Icon = iconFor(scan);
          const badgeClass = scan.highest_severity
            ? SEVERITY_BADGE[scan.highest_severity]
            : "bg-severity-low/15 text-severity-low";
          const label = scan.highest_severity
            ? `${scan.total_findings} risco${scan.total_findings === 1 ? "" : "s"}`
            : "0 riscos";

          return (
            <li key={scan.id} className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-3 min-w-0">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${badgeClass}`}>
                  <Icon size={16} />
                </div>
                <div className="min-w-0">
                  <div className="text-sm text-gray-200 truncate">{scan.domain_hostname}</div>
                  <div className="text-xs text-gray-500">Concluída em {formatDate(scan.finished_at)}</div>
                </div>
              </div>
              <span className={`text-xs font-medium px-2.5 py-1 rounded-full shrink-0 ${badgeClass}`}>
                {label}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
