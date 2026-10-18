"use client";

import { CheckCircle2, Circle, Clock, XCircle } from "lucide-react";
import ScanProgressRing from "./ScanProgressRing";

export interface ScanStep {
  label: string;
  done: boolean;
}

interface ScanProgressPanelProps {
  percent: number;
  steps: ScanStep[];
  elapsed: string;
  onCancel?: () => void;
}

export default function ScanProgressPanel({ percent, steps, elapsed, onCancel }: ScanProgressPanelProps) {
  return (
    <div className="rounded-xl border border-bg-border bg-bg-panel p-6">
      <h3 className="text-white font-semibold mb-4">Varredura em Andamento</h3>

      <div className="flex items-center gap-8">
        <ScanProgressRing percent={percent} />

        <ul className="flex-1 space-y-2.5">
          {steps.map((step) => (
            <li key={step.label} className="flex items-center gap-2.5 text-sm">
              {step.done ? (
                <CheckCircle2 size={16} className="text-severity-low shrink-0" />
              ) : (
                <Circle size={16} className="text-gray-600 shrink-0" />
              )}
              <span className={step.done ? "text-gray-300" : "text-gray-500"}>{step.label}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="flex items-center justify-between mt-6 pt-4 border-t border-bg-border">
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <Clock size={16} />
          Tempo decorrido <span className="text-gray-200 font-medium">{elapsed}</span>
        </div>
        <button
          onClick={onCancel}
          className="flex items-center gap-2 text-sm text-brand-red border border-brand-red/40 hover:bg-brand-red/10 px-4 py-2 rounded-lg transition-colors"
        >
          <XCircle size={16} />
          Cancelar Varredura
        </button>
      </div>
    </div>
  );
}
