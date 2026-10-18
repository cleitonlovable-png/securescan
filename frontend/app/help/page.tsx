import Topbar from "@/components/Topbar";
import { HelpCircle } from "lucide-react";

export default function HelpPage() {
  return (
    <>
      <Topbar userName="Administrador" userRole="Modo local" />
      <div className="p-8">
        <div className="rounded-xl border border-bg-border bg-bg-panel p-8 max-w-2xl">
          <div className="flex items-center gap-2 mb-4">
            <HelpCircle className="text-brand-red" size={22} />
            <h2 className="text-white font-semibold text-lg">Ajuda</h2>
          </div>
          <div className="space-y-3 text-sm text-gray-400">
            <p>
              <strong className="text-gray-200">Como escanear algo:</strong> vá em Dashboard, cole a URL do seu
              app (ex: <code className="text-gray-300">http://127.0.0.1:5000</code> ou um domínio seu) e clique em
              &quot;Iniciar Varredura&quot;.
            </p>
            <p>
              <strong className="text-gray-200">Sobre o modo local:</strong> nesta versão, todo mundo que abre o
              SecureScan usa automaticamente a mesma conta/organização local — não há cadastro ainda. Isso está
              documentado em <code className="text-gray-300">docs/SECURITY_MODEL.md</code>.
            </p>
            <p>
              <strong className="text-gray-200">Módulos ainda não prontos:</strong> Análise de Código, Pagamentos,
              Relatórios em PDF e Integrações aparecem no menu mas ainda estão no roadmap — ver{" "}
              <code className="text-gray-300">docs/ROADMAP.md</code>.
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
