"use client";

import { useEffect, useState } from "react";
import { Radar, Bell, RefreshCw, Download } from "lucide-react";
import Link from "next/link";
import { checkSystemUpdate, applySystemUpdate, UpdateCheckResponse } from "@/lib/api";

interface TopbarProps {
  userName?: string;
  userRole?: string;
}

export default function Topbar({ userName = "Usuário", userRole = "Administrador" }: TopbarProps) {
  const [updateInfo, setUpdateInfo] = useState<UpdateCheckResponse | null>(null);
  const [checking, setChecking] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const initials = userName
    .split(" ")
    .map((p) => p[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  async function handleCheckUpdates(manual = false) {
    setChecking(true);
    if (manual) setStatusMsg(null);
    try {
      const info = await checkSystemUpdate();
      setUpdateInfo(info);
      if (manual && !info.update_available) {
        setStatusMsg(`Atualizado (v${info.current_version})`);
        setTimeout(() => setStatusMsg(null), 4000);
      }
    } catch {
      if (manual) {
        setStatusMsg("Sem conexão com o servidor de atualização");
        setTimeout(() => setStatusMsg(null), 4000);
      }
    } finally {
      setChecking(false);
    }
  }

  async function handleInstallUpdate() {
    if (!updateInfo) return;
    setUpdating(true);
    setStatusMsg("Baixando e instalando atualização...");
    try {
      const res = await applySystemUpdate();
      setStatusMsg(res.message);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Falha ao atualizar.";
      setStatusMsg(msg);
      setUpdating(false);
    }
  }

  useEffect(() => {
    handleCheckUpdates(false);
  }, []);

  return (
    <header className="flex items-center justify-between px-8 py-5 border-b border-bg-border">
      <div>
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold text-white">
            Varredura completa. Mais segurança para o seu negócio.
          </h1>
          {updateInfo?.current_version && (
            <span className="text-xs px-2 py-0.5 rounded bg-bg-card border border-bg-border text-gray-400">
              v{updateInfo.current_version}
            </span>
          )}
        </div>
        <p className="text-sm text-gray-500 mt-0.5">
          Detecta vulnerabilidades, invasões, vazamentos e muito mais em sua aplicação web, SaaS e infraestrutura.
        </p>
      </div>

      <div className="flex items-center gap-4">
        {statusMsg && (
          <span className="text-xs px-3 py-1.5 rounded bg-brand-red/10 border border-brand-red/30 text-gray-200">
            {statusMsg}
          </span>
        )}

        {updateInfo?.update_available ? (
          <button
            onClick={handleInstallUpdate}
            disabled={updating}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-brand-red hover:bg-red-700 text-white text-xs font-semibold transition-colors disabled:opacity-50"
            title={updateInfo.notes || `Nova versão v${updateInfo.latest_version} disponível`}
          >
            <Download size={14} />
            {updating ? "Atualizando..." : `Atualizar para v${updateInfo.latest_version}`}
          </button>
        ) : (
          <button
            onClick={() => handleCheckUpdates(true)}
            disabled={checking}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-bg-card border border-bg-border text-gray-400 hover:text-white text-xs transition-colors disabled:opacity-50"
            title="Verificar se há novas atualizações disponíveis"
          >
            <RefreshCw size={14} className={checking ? "animate-spin" : ""} />
            {checking ? "Verificando..." : "Verificar atualização"}
          </button>
        )}

        <Link href="/scan/new" className="text-gray-400 hover:text-white transition-colors" aria-label="Nova varredura" title="Nova varredura">
          <Radar size={20} />
        </Link>
        <button
          className="text-gray-400 hover:text-white transition-colors"
          aria-label="Notificações"
          title="Notificações do sistema"
        >
          <Bell size={20} />
        </button>

        <div className="flex items-center gap-2 pl-4 border-l border-bg-border">
          <div className="w-9 h-9 rounded-full bg-brand-red/20 text-brand-red flex items-center justify-center font-semibold text-sm">
            {initials}
          </div>
          <div className="text-sm">
            <div className="text-white font-medium leading-tight">{userName}</div>
            <div className="text-gray-500 text-xs leading-tight">{userRole}</div>
          </div>
        </div>
      </div>
    </header>
  );
}

