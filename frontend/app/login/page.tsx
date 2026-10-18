"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ShieldCheck } from "lucide-react";
import { login } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao entrar.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-bg">
      <form onSubmit={handleSubmit} className="w-full max-w-sm rounded-xl border border-bg-border bg-bg-panel p-8">
        <div className="flex items-center gap-2 mb-6">
          <ShieldCheck className="text-brand-red" size={28} />
          <span className="font-bold text-white text-lg">SecureScan</span>
        </div>

        {error && (
          <div className="mb-4 text-sm text-severity-critical bg-severity-critical/10 border border-severity-critical/30 rounded-lg px-3 py-2">
            {error}
          </div>
        )}

        <label className="block text-sm text-gray-400 mb-1">E-mail</label>
        <input
          type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
          className="w-full mb-4 bg-bg border border-bg-border rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-brand-red/50"
        />

        <label className="block text-sm text-gray-400 mb-1">Senha</label>
        <input
          type="password" required value={password} onChange={(e) => setPassword(e.target.value)}
          className="w-full mb-6 bg-bg border border-bg-border rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-brand-red/50"
        />

        <button
          type="submit" disabled={loading}
          className="w-full bg-brand-red hover:bg-brand-red/90 disabled:opacity-50 text-white text-sm font-semibold py-2.5 rounded-lg transition-colors"
        >
          {loading ? "Entrando..." : "Entrar"}
        </button>

        <p className="text-xs text-gray-500 text-center mt-4">
          Não tem conta? <a href="/register" className="text-brand-red hover:underline">Criar conta</a>
        </p>
      </form>
    </div>
  );
}
