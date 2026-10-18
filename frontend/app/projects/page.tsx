"use client";

import { useEffect, useState } from "react";
import { FolderKanban } from "lucide-react";
import Topbar from "@/components/Topbar";
import { ensureSession, getDefaultOrganizationId, listProjects, ProjectItem } from "@/lib/api";

function scoreColor(score: number | null): string {
  if (score === null) return "text-gray-500";
  if (score >= 75) return "text-severity-low";
  if (score >= 50) return "text-severity-medium";
  if (score >= 25) return "text-severity-high";
  return "text-severity-critical";
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<ProjectItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        await ensureSession();
        const orgId = await getDefaultOrganizationId();
        setProjects(await listProjects(orgId));
      } catch (e) {
        setError(e instanceof Error ? e.message : "Erro ao carregar projetos.");
      }
    })();
  }, []);

  return (
    <>
      <Topbar userName="Administrador" userRole="Modo local" />
      <div className="p-8 space-y-6">
        <div>
          <h2 className="text-white font-semibold text-lg">Meus Projetos</h2>
          <p className="text-sm text-gray-500">
            Todo alvo escaneado pela tela de Nova Varredura vira um projeto aqui automaticamente.
          </p>
        </div>

        {error && (
          <div className="rounded-xl border border-severity-critical/40 bg-severity-critical/10 text-severity-critical text-sm px-4 py-3">
            {error}
          </div>
        )}

        {projects === null && !error && <div className="text-sm text-gray-500">Carregando...</div>}

        {projects && projects.length === 0 && (
          <div className="rounded-xl border border-bg-border bg-bg-panel p-6 text-center text-gray-500 text-sm">
            Nenhum projeto ainda. Rode uma varredura no <a href="/" className="text-brand-red hover:underline">Dashboard</a> para criar o primeiro.
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects?.map((p) => (
            <div key={p.id} className="rounded-xl border border-bg-border bg-bg-panel p-5">
              <div className="flex items-center gap-2 mb-2">
                <FolderKanban className="text-brand-red" size={18} />
                <span className="text-white font-medium">{p.name}</span>
              </div>
              <p className="text-xs text-gray-500 mb-3">{p.description || "Sem descrição."}</p>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-500 capitalize">{p.environment}</span>
                <span className={`font-bold ${scoreColor(p.security_score)}`}>
                  {p.security_score !== null ? `${p.security_score}/100` : "—"}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
