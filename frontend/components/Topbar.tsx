"use client";

import { Radar, Bell } from "lucide-react";
import Link from "next/link";

interface TopbarProps {
  userName?: string;
  userRole?: string;
}

export default function Topbar({ userName = "Usuário", userRole = "Administrador" }: TopbarProps) {
  const initials = userName
    .split(" ")
    .map((p) => p[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <header className="flex items-center justify-between px-8 py-5 border-b border-bg-border">
      <div>
        <h1 className="text-lg font-semibold text-white">
          Varredura completa. Mais segurança para o seu negócio.
        </h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Detecta vulnerabilidades, invasões, vazamentos e muito mais em sua aplicação web, SaaS e infraestrutura.
        </p>
      </div>

      <div className="flex items-center gap-5">
        <Link href="/scan/new" className="text-gray-400 hover:text-white transition-colors" aria-label="Nova varredura" title="Nova varredura">
          <Radar size={20} />
        </Link>
        <button
          className="text-gray-400 hover:text-white transition-colors"
          aria-label="Notificações"
          title="Ainda não há sistema de notificações — em breve"
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
