import { AlertOctagon, AlertTriangle, Info, CheckCircle2, LucideIcon } from "lucide-react";

interface SeverityCardProps {
  label: string;
  count: number;
  description: string;
  variant: "critical" | "high" | "medium" | "low";
}

const VARIANT_MAP: Record<
  SeverityCardProps["variant"],
  { icon: LucideIcon; color: string; bg: string; border: string }
> = {
  critical: { icon: AlertOctagon, color: "text-severity-critical", bg: "bg-severity-critical/10", border: "border-severity-critical/30" },
  high: { icon: AlertTriangle, color: "text-severity-high", bg: "bg-severity-high/10", border: "border-severity-high/30" },
  medium: { icon: Info, color: "text-severity-medium", bg: "bg-severity-medium/10", border: "border-severity-medium/30" },
  low: { icon: CheckCircle2, color: "text-severity-low", bg: "bg-severity-low/10", border: "border-severity-low/30" },
};

export default function SeverityCard({ label, count, description, variant }: SeverityCardProps) {
  const { icon: Icon, color, bg, border } = VARIANT_MAP[variant];

  return (
    <div className={`rounded-xl border ${border} ${bg} p-5 flex items-center gap-4`}>
      <div className={`w-11 h-11 rounded-lg ${bg} flex items-center justify-center ${color}`}>
        <Icon size={22} />
      </div>
      <div>
        <div className={`text-2xl font-bold ${color}`}>{count}</div>
        <div className="text-sm text-gray-200 font-medium">{label}</div>
        <div className="text-xs text-gray-500">{description}</div>
      </div>
    </div>
  );
}
