import {
  Globe, Code2, KeyRound, Cloud, Database, Server,
  CreditCard, Share2, Settings, FileText, LucideIcon,
} from "lucide-react";

interface ModuleCardData {
  title: string;
  description: string;
  icon: LucideIcon;
}

const MODULES: ModuleCardData[] = [
  { title: "Vulnerabilidades Web", description: "SQL Injection, XSS, CSRF, Clickjacking, etc.", icon: Globe },
  { title: "Análise de Código", description: "Código-fonte, bibliotecas, dependências vulneráveis.", icon: Code2 },
  { title: "Chaves e Secrets", description: ".env, chaves API, tokens, credenciais expostas.", icon: KeyRound },
  { title: "APIs e Endpoints", description: "REST, GraphQL, autenticação, rate limit, exposição de dados.", icon: Cloud },
  { title: "Banco de Dados", description: "Acessos, permissões, dados sensíveis.", icon: Database },
  { title: "Infraestrutura", description: "Configurações, portas, serviços expostos.", icon: Server },
  { title: "Pagamentos / Checkout", description: "Testes de segurança no fluxo de pagamento (Stripe, Asaas, etc.).", icon: CreditCard },
  { title: "SaaS e Terceiros", description: "Integrações, SDKs, serviços externos.", icon: Share2 },
  { title: "Configurações e Headers", description: "SSL/TLS, CORS, headers de segurança.", icon: Settings },
  { title: "Relatório Completo", description: "PDF/HTML com evidências e recomendações.", icon: FileText },
];

export default function ModuleGrid() {
  return (
    <div>
      <h3 className="text-white font-semibold mb-1">Módulos de Análise</h3>
      <p className="text-sm text-gray-500 mb-4">Tudo o que sua aplicação precisa, em uma única varredura.</p>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {MODULES.map(({ title, description, icon: Icon }) => (
          <div key={title} className="rounded-xl border border-bg-border bg-bg-panel p-4 hover:border-brand-red/30 transition-colors">
            <div className="w-9 h-9 rounded-lg bg-brand-red/15 text-brand-red flex items-center justify-center mb-3">
              <Icon size={18} />
            </div>
            <div className="text-sm font-medium text-gray-200 mb-1">{title}</div>
            <div className="text-xs text-gray-500">{description}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
