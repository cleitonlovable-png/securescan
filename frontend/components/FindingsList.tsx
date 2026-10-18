import { ShieldAlert } from "lucide-react";

interface FindingItem {
  id: string;
  title: string;
  description: string;
  severity: string;
  remediation: string | null;
  endpoint_or_file: string | null;
}

const SEVERITY_BORDER: Record<string, string> = {
  critical: "border-severity-critical",
  high: "border-severity-high",
  medium: "border-severity-medium",
  low: "border-severity-low",
  info: "border-gray-600",
};

const SEVERITY_BADGE: Record<string, string> = {
  critical: "bg-severity-critical/15 text-severity-critical",
  high: "bg-severity-high/15 text-severity-high",
  medium: "bg-severity-medium/15 text-severity-medium",
  low: "bg-severity-low/15 text-severity-low",
  info: "bg-gray-600/15 text-gray-400",
};

const SEVERITY_LABEL: Record<string, string> = {
  critical: "Crítica",
  high: "Alta",
  medium: "Média",
  low: "Baixa",
  info: "Info",
};

interface FindingsListProps {
  findings: FindingItem[];
}

export default function FindingsList({ findings }: FindingsListProps) {
  if (findings.length === 0) {
    return (
      <div className="rounded-xl border border-bg-border bg-bg-panel p-6 text-center text-gray-500 text-sm">
        Nenhum achado registrado nesta varredura. ✅
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-bg-border bg-bg-panel p-6">
      <div className="flex items-center gap-2 mb-4">
        <ShieldAlert className="text-brand-red" size={18} />
        <h3 className="text-white font-semibold">Achados desta varredura</h3>
      </div>

      <div className="space-y-3">
        {findings.map((f) => (
          <div key={f.id} className={`rounded-lg border-l-4 ${SEVERITY_BORDER[f.severity] || "border-gray-600"} bg-bg p-4`}>
            <div className="flex items-center justify-between gap-3 mb-1">
              <span className="text-sm font-medium text-gray-200">{f.title}</span>
              <span className={`text-[11px] font-semibold uppercase px-2 py-0.5 rounded-full shrink-0 ${SEVERITY_BADGE[f.severity]}`}>
                {SEVERITY_LABEL[f.severity] || f.severity}
              </span>
            </div>
            {f.description && <p className="text-xs text-gray-500 mb-1">{f.description}</p>}
            {f.remediation && (
              <p className="text-xs text-gray-300 bg-white/5 rounded px-2 py-1.5 mt-1">
                💡 {f.remediation}
              </p>
            )}
            {f.endpoint_or_file && (
              <p className="text-[11px] text-gray-600 mt-1 truncate">{f.endpoint_or_file}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
