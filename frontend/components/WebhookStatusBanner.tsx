"use client";

import { Send, CheckCircle2, XCircle } from "lucide-react";

interface WebhookStatusBannerProps {
  status: "sent" | "failed" | null;
  error: string | null;
}

export default function WebhookStatusBanner({ status, error }: WebhookStatusBannerProps) {
  if (!status) return null; // sem webhook configurado — não mostra nada

  if (status === "sent") {
    return (
      <div className="rounded-xl border border-severity-low/30 bg-severity-low/10 px-4 py-3 flex items-center gap-2 text-sm text-severity-low">
        <CheckCircle2 size={16} />
        Relatório enviado com sucesso para o webhook configurado.
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-severity-critical/30 bg-severity-critical/10 px-4 py-3 flex items-start gap-2 text-sm text-severity-critical">
      <XCircle size={16} className="shrink-0 mt-0.5" />
      <div>
        <div className="font-medium">Falha ao enviar o relatório via webhook.</div>
        {error && <div className="text-xs text-severity-critical/80 mt-1">{error}</div>}
        <div className="text-xs text-gray-400 mt-1">
          Confira a URL e o segredo em Configurações — os achados desta varredura continuam salvos normalmente.
        </div>
      </div>
    </div>
  );
}
