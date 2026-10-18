"use client";

import { useEffect, useState } from "react";
import { Settings, Webhook, RefreshCw, Copy, Check, Building2, Users, Plus, Trash2 } from "lucide-react";
import Topbar from "@/components/Topbar";
import {
  ensureSession, getDefaultOrganizationId, getWebhookSettings,
  updateWebhookSettings, generateWebhookSecret,
  listOrganizations, createOrganization, setActiveOrganization,
  listMembers, inviteMember, removeMember,
  OrganizationItem, MemberItem,
} from "@/lib/api";

const ROLE_LABELS: Record<string, string> = {
  OWNER: "Dono", ADMIN: "Administrador", SECURITY_ANALYST: "Analista de Segurança",
  DEVELOPER: "Desenvolvedor", VIEWER: "Visualizador",
};

export default function SettingsPage() {
  const [orgId, setOrgId] = useState<string | null>(null);
  const [initError, setInitError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  // webhook
  const [webhookUrl, setWebhookUrl] = useState("");
  const [webhookSecret, setWebhookSecret] = useState("");
  const [slackWebhookUrl, setSlackWebhookUrl] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [copied, setCopied] = useState(false);

  // organizações
  const [organizations, setOrganizations] = useState<OrganizationItem[]>([]);
  const [newOrgName, setNewOrgName] = useState("");

  // membros
  const [members, setMembers] = useState<MemberItem[]>([]);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("VIEWER");

  async function loadAll(currentOrgId: string) {
    const [settings, orgs, memberList] = await Promise.all([
      getWebhookSettings(currentOrgId),
      listOrganizations(),
      listMembers(currentOrgId),
    ]);
    setWebhookUrl(settings.webhook_url || "");
    setWebhookSecret(settings.webhook_secret || "");
    setSlackWebhookUrl(settings.slack_webhook_url || "");
    setOrganizations(orgs);
    setMembers(memberList);
  }

  useEffect(() => {
    (async () => {
      try {
        await ensureSession();
        const id = await getDefaultOrganizationId();
        setOrgId(id);
        await loadAll(id);
      } catch (e) {
        setInitError(e instanceof Error ? e.message : "Erro ao carregar configurações.");
      }
    })();
  }, []);

  async function handleSaveWebhook() {
    if (!orgId) return;
    setSaving(true);
    setSaved(false);
    try {
      await updateWebhookSettings(orgId, {
        webhook_url: webhookUrl.trim() || null,
        webhook_secret: webhookSecret.trim() || null,
        slack_webhook_url: slackWebhookUrl.trim() || null,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (e) {
      setInitError(e instanceof Error ? e.message : "Erro ao salvar.");
    } finally {
      setSaving(false);
    }
  }

  async function handleGenerateSecret() {
    if (!orgId) return;
    try {
      const settings = await generateWebhookSecret(orgId);
      setWebhookSecret(settings.webhook_secret || "");
    } catch (e) {
      setInitError(e instanceof Error ? e.message : "Erro ao gerar segredo.");
    }
  }

  function handleCopySecret() {
    navigator.clipboard.writeText(webhookSecret);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  async function handleSwitchOrg(id: string) {
    setActiveOrganization(id);
    setOrgId(id);
    setActionMessage(null);
    try {
      await loadAll(id);
    } catch (e) {
      setInitError(e instanceof Error ? e.message : "Erro ao trocar de organização.");
    }
  }

  async function handleCreateOrg() {
    if (!newOrgName.trim()) return;
    try {
      const org = await createOrganization(newOrgName.trim());
      setNewOrgName("");
      await handleSwitchOrg(org.id); // já troca pra organização nova
    } catch (e) {
      setInitError(e instanceof Error ? e.message : "Erro ao criar organização.");
    }
  }

  async function handleInvite() {
    if (!orgId || !inviteEmail.trim()) return;
    setActionMessage(null);
    try {
      await inviteMember(orgId, inviteEmail.trim(), inviteRole);
      setInviteEmail("");
      setMembers(await listMembers(orgId));
      setActionMessage("Membro adicionado com sucesso.");
    } catch (e) {
      setActionMessage(e instanceof Error ? e.message : "Erro ao convidar membro.");
    }
  }

  async function handleRemoveMember(membershipId: string) {
    if (!orgId) return;
    try {
      await removeMember(orgId, membershipId);
      setMembers(await listMembers(orgId));
    } catch (e) {
      setActionMessage(e instanceof Error ? e.message : "Erro ao remover membro.");
    }
  }

  return (
    <>
      <Topbar userName="Administrador" userRole="Modo local" />
      <div className="p-8 space-y-6">
        <div>
          <h2 className="text-white font-semibold text-lg flex items-center gap-2">
            <Settings size={20} className="text-brand-red" /> Configurações
          </h2>
        </div>

        {initError && (
          <div className="rounded-xl border border-severity-critical/40 bg-severity-critical/10 text-severity-critical text-sm px-4 py-3">
            {initError}
          </div>
        )}

        {/* Organizações */}
        <div className="rounded-xl border border-bg-border bg-bg-panel p-6 max-w-2xl">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-brand-red/15 text-brand-red flex items-center justify-center">
              <Building2 size={20} />
            </div>
            <div>
              <h3 className="text-white font-semibold">Organizações</h3>
              <p className="text-sm text-gray-500">Troque entre organizações ou crie uma nova.</p>
            </div>
          </div>

          <div className="space-y-2 mb-4">
            {organizations.map((org) => (
              <button
                key={org.id}
                onClick={() => handleSwitchOrg(org.id)}
                className={`w-full text-left px-4 py-2.5 rounded-lg text-sm border transition-colors ${
                  org.id === orgId
                    ? "border-brand-red/50 bg-brand-red/10 text-white"
                    : "border-bg-border text-gray-300 hover:border-brand-red/30"
                }`}
              >
                {org.name} {org.id === orgId && <span className="text-brand-red text-xs ml-2">(ativa)</span>}
              </button>
            ))}
          </div>

          <div className="flex gap-2">
            <input
              value={newOrgName} onChange={(e) => setNewOrgName(e.target.value)}
              placeholder="Nome da nova organização"
              className="flex-1 bg-bg border border-bg-border rounded-lg px-3 py-2 text-sm text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-brand-red/50"
            />
            <button
              onClick={handleCreateOrg}
              className="flex items-center gap-1.5 text-sm text-white bg-brand-red hover:bg-brand-red/90 px-4 py-2 rounded-lg transition-colors"
            >
              <Plus size={14} /> Criar
            </button>
          </div>
        </div>

        {/* Membros */}
        <div className="rounded-xl border border-bg-border bg-bg-panel p-6 max-w-2xl">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-brand-red/15 text-brand-red flex items-center justify-center">
              <Users size={20} />
            </div>
            <div>
              <h3 className="text-white font-semibold">Membros da organização ativa</h3>
              <p className="text-sm text-gray-500">
                A pessoa precisa já ter uma conta no SecureScan (criada em /register).
              </p>
            </div>
          </div>

          {actionMessage && (
            <div className="mb-3 text-xs text-gray-300 bg-bg border border-bg-border rounded-lg px-3 py-2">
              {actionMessage}
            </div>
          )}

          <div className="space-y-2 mb-4">
            {members.map((m) => (
              <div key={m.id} className="flex items-center justify-between px-4 py-2.5 rounded-lg border border-bg-border text-sm">
                <div>
                  <span className="text-gray-200">{m.full_name}</span>
                  <span className="text-gray-500 ml-2 text-xs">{m.email}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-gray-400">{ROLE_LABELS[m.role] || m.role}</span>
                  {m.role !== "OWNER" && (
                    <button onClick={() => handleRemoveMember(m.id)} className="text-gray-500 hover:text-severity-critical">
                      <Trash2 size={14} />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="flex gap-2">
            <input
              value={inviteEmail} onChange={(e) => setInviteEmail(e.target.value)}
              placeholder="email@dapessoa.com"
              className="flex-1 bg-bg border border-bg-border rounded-lg px-3 py-2 text-sm text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-brand-red/50"
            />
            <select
              value={inviteRole} onChange={(e) => setInviteRole(e.target.value)}
              className="bg-bg border border-bg-border rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-brand-red/50"
            >
              {Object.entries(ROLE_LABELS).filter(([k]) => k !== "OWNER").map(([k, label]) => (
                <option key={k} value={k}>{label}</option>
              ))}
            </select>
            <button
              onClick={handleInvite}
              className="flex items-center gap-1.5 text-sm text-white bg-brand-red hover:bg-brand-red/90 px-4 py-2 rounded-lg transition-colors whitespace-nowrap"
            >
              <Plus size={14} /> Adicionar
            </button>
          </div>
        </div>

        {/* Webhook + Slack */}
        <div className="rounded-xl border border-bg-border bg-bg-panel p-6 max-w-2xl">
          <div className="flex items-center gap-3 mb-1">
            <div className="w-10 h-10 rounded-lg bg-brand-red/15 text-brand-red flex items-center justify-center">
              <Webhook size={20} />
            </div>
            <div>
              <h3 className="text-white font-semibold">Integrações</h3>
              <p className="text-sm text-gray-500">
                Webhook genérico (relatório completo em JSON) e/ou notificação no Slack
                (só quando houver achado crítico/alto).
              </p>
            </div>
          </div>

          <div className="mt-4 space-y-3">
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">URL do webhook (JSON)</label>
              <input
                value={webhookUrl} onChange={(e) => setWebhookUrl(e.target.value)}
                placeholder="http://host.docker.internal:4000/webhooks/securescan"
                className="w-full bg-bg border border-bg-border rounded-lg px-4 py-2.5 text-sm text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-brand-red/50"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">Segredo compartilhado</label>
              <div className="flex gap-2">
                <input
                  value={webhookSecret} onChange={(e) => setWebhookSecret(e.target.value)}
                  placeholder="Gere um segredo ou cole o seu"
                  className="flex-1 bg-bg border border-bg-border rounded-lg px-4 py-2.5 text-sm text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-brand-red/50 font-mono"
                />
                <button onClick={handleGenerateSecret} title="Gerar novo segredo"
                  className="shrink-0 flex items-center gap-1.5 text-sm text-gray-300 border border-bg-border hover:border-brand-red/40 px-3 py-2 rounded-lg transition-colors">
                  <RefreshCw size={14} /> Gerar
                </button>
                <button onClick={handleCopySecret} disabled={!webhookSecret} title="Copiar"
                  className="shrink-0 flex items-center gap-1.5 text-sm text-gray-300 border border-bg-border hover:border-brand-red/40 disabled:opacity-40 px-3 py-2 rounded-lg transition-colors">
                  {copied ? <Check size={14} className="text-severity-low" /> : <Copy size={14} />}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">Slack — URL do Incoming Webhook (opcional)</label>
              <input
                value={slackWebhookUrl} onChange={(e) => setSlackWebhookUrl(e.target.value)}
                placeholder="https://hooks.slack.com/services/..."
                className="w-full bg-bg border border-bg-border rounded-lg px-4 py-2.5 text-sm text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-brand-red/50"
              />
            </div>

            <button
              onClick={handleSaveWebhook} disabled={saving}
              className="bg-brand-red hover:bg-brand-red/90 disabled:opacity-50 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition-colors"
            >
              {saving ? "Salvando..." : saved ? "Salvo ✓" : "Salvar"}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
