import { Construction } from "lucide-react";
import Topbar from "./Topbar";

interface ComingSoonProps {
  title: string;
  phase: string;
}

export default function ComingSoon({ title, phase }: ComingSoonProps) {
  return (
    <>
      <Topbar userName="Administrador" userRole="Modo local" />
      <div className="p-8">
        <div className="rounded-xl border border-bg-border bg-bg-panel p-12 flex flex-col items-center text-center gap-3">
          <Construction className="text-gray-600" size={36} />
          <h2 className="text-white font-semibold text-lg">{title}</h2>
          <p className="text-sm text-gray-500 max-w-md">
            Este módulo ainda não foi construído — está planejado para a{" "}
            <span className="text-gray-300 font-medium">{phase}</span> do roadmap
            (ver <code className="text-gray-400">docs/ROADMAP.md</code> no projeto).
          </p>
          <a href="/" className="text-sm text-brand-red hover:underline mt-2">← Voltar para o Dashboard</a>
        </div>
      </div>
    </>
  );
}
