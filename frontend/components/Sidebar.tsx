"use client";

import {
  LayoutDashboard, Search, FolderKanban, FileText, ShieldAlert, Globe,
  Code2, KeyRound, Database, Server, CreditCard, Settings, Share2,
  History, HelpCircle, ShieldCheck, Zap,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { label: "Dashboard", href: "/", icon: LayoutDashboard },
  { label: "Nova Varredura", href: "/scan/new", icon: Search },
  { label: "Teste de Invasão", href: "/pentest", icon: Zap },
  { label: "Meus Projetos", href: "/projects", icon: FolderKanban },
  { label: "Relatórios", href: "/reports", icon: FileText },
  { label: "Vulnerabilidades", href: "/findings", icon: ShieldAlert },
  { label: "Segurança de API", href: "/api-security", icon: Globe },
  { label: "Análise de Código", href: "/code", icon: Code2 },
  { label: "Chaves e Secrets", href: "/secrets", icon: KeyRound },
  { label: "Banco de Dados", href: "/database", icon: Database },
  { label: "Infraestrutura", href: "/infra", icon: Server },
  { label: "Pagamentos / Checkout", href: "/payments", icon: CreditCard },
  { label: "Configurações", href: "/settings", icon: Settings },
  { label: "Integrações", href: "/integrations", icon: Share2 },
  { label: "Histórico", href: "/history", icon: History },
  { label: "Ajuda", href: "/help", icon: HelpCircle },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 shrink-0 border-r border-bg-border bg-bg-panel flex flex-col h-screen sticky top-0">
      <div className="flex items-center gap-2 px-5 py-5">
        <ShieldCheck className="text-brand-red" size={28} strokeWidth={2.2} />
        <div>
          <div className="font-bold text-white leading-tight">SecureScan</div>
          <div className="text-[11px] text-gray-500 leading-tight">Sua aplicação mais segura</div>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-2 space-y-1">
        {NAV_ITEMS.map(({ label, href, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                active
                  ? "bg-brand-red/15 text-brand-red border border-brand-red/30"
                  : "text-gray-400 hover:bg-bg-panelHover hover:text-gray-200"
              }`}
            >
              <Icon size={18} />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="m-3 rounded-xl border border-brand-red/30 bg-brand-red/10 p-4 text-sm text-gray-200">
        <ShieldCheck className="text-brand-red mb-2" size={20} />
        Segurança hoje, menos problemas amanhã.
      </div>
    </aside>
  );
}
