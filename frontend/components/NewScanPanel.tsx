"use client";

import { useState } from "react";
import { Target, Globe } from "lucide-react";
import SavedTargets from "./SavedTargets";

const CHECKS = [
  "Varredura completa",
  "Incluir subdomínios",
  "Análise de código",
  "Verificar segredos",
];

const RIGHT_LIST = ["Web", "API", "Banco de Dados", "Infraestrutura", "Pagamentos", "Arquivos e Secrets", "Tudo em um só lugar"];

interface NewScanPanelProps {
  onStartScan?: (url: string) => void;
}

export default function NewScanPanel({ onStartScan }: NewScanPanelProps) {
  const [url, setUrl] = useState("");
  const [checked, setChecked] = useState<Record<string, boolean>>(
    Object.fromEntries(CHECKS.map((c) => [c, true]))
  );

  return (
    <div className="rounded-xl border border-bg-border bg-bg-panel p-6">
      <div className="flex items-start justify-between gap-6">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-1">
            <div className="w-10 h-10 rounded-lg bg-brand-red/15 text-brand-red flex items-center justify-center">
              <Target size={20} />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">Nova Varredura</h2>
              <p className="text-sm text-gray-500">
                Informe a URL da sua aplicação ou selecione um projeto para iniciar a análise completa.
              </p>
            </div>
          </div>

          <div className="flex gap-3 mt-4">
            <input
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://seudominio.com"
              className="flex-1 bg-bg border border-bg-border rounded-lg px-4 py-2.5 text-sm text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-brand-red/50"
            />
            <button
              onClick={() => onStartScan?.(url)}
              className="bg-brand-red hover:bg-brand-red/90 text-white text-sm font-semibold px-5 py-2.5 rounded-lg whitespace-nowrap transition-colors"
            >
              Iniciar Varredura →
            </button>
          </div>

          <SavedTargets storageKey="securescan_saved_targets_dashboard" currentValue={url} onSelect={setUrl} />

          <div className="flex flex-wrap gap-x-6 gap-y-2 mt-4">
            {CHECKS.map((label) => (
              <label key={label} className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={checked[label]}
                  onChange={() => setChecked((s) => ({ ...s, [label]: !s[label] }))}
                  className="accent-brand-red w-4 h-4"
                />
                {label}
              </label>
            ))}
          </div>

          <p className="text-[11px] text-gray-600 mt-3">
            Quer testar invasão de verdade (payloads reais de ataque)? Use a aba{" "}
            <a href="/pentest" className="text-brand-red hover:underline">Teste de Invasão</a> no menu.
          </p>
        </div>

        <div className="hidden lg:flex flex-col items-center gap-3 shrink-0 w-56">
          <div className="w-40 h-40 rounded-xl bg-bg border border-bg-border flex items-center justify-center text-brand-red/40">
            <Globe size={64} />
          </div>
          <ul className="w-full space-y-1.5">
            {RIGHT_LIST.map((item) => (
              <li key={item} className="flex items-center gap-2 text-xs text-gray-400">
                <span className="text-severity-low">✓</span> {item}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
