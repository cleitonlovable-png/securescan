"use client";

import { useEffect, useState } from "react";
import Topbar from "./Topbar";
import FindingsList from "./FindingsList";
import { ensureSession, getDefaultOrganizationId, listVulnerabilities, VulnerabilityItem } from "@/lib/api";

interface VulnerabilitiesViewProps {
  title: string;
  subtitle: string;
  category?: string;
}

export default function VulnerabilitiesView({ title, subtitle, category }: VulnerabilitiesViewProps) {
  const [items, setItems] = useState<VulnerabilityItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        await ensureSession();
        const orgId = await getDefaultOrganizationId();
        const data = await listVulnerabilities(orgId, category);
        setItems(data);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Erro ao carregar dados.");
      }
    })();
  }, [category]);

  return (
    <>
      <Topbar userName="Administrador" userRole="Modo local" />
      <div className="p-8 space-y-6">
        <div>
          <h2 className="text-white font-semibold text-lg">{title}</h2>
          <p className="text-sm text-gray-500">{subtitle}</p>
        </div>

        {error && (
          <div className="rounded-xl border border-severity-critical/40 bg-severity-critical/10 text-severity-critical text-sm px-4 py-3">
            {error}
          </div>
        )}

        {items === null && !error && (
          <div className="text-sm text-gray-500">Carregando...</div>
        )}

        {items !== null && (
          <>
            {items.length === 0 ? (
              <div className="rounded-xl border border-bg-border bg-bg-panel p-6 text-center text-gray-500 text-sm">
                Nenhum achado ainda nesta categoria. Rode uma varredura completa na tela de{" "}
                <a href="/" className="text-brand-red hover:underline">Dashboard</a> para popular esta lista.
              </div>
            ) : (
              <FindingsList findings={items} />
            )}
          </>
        )}
      </div>
    </>
  );
}
