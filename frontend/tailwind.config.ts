import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Paleta "dark cybersecurity dashboard" — Seção 27 do prompt original
        bg: {
          DEFAULT: "#0a0e14",   // fundo geral, quase preto
          panel: "#111722",     // cards e painéis
          panelHover: "#161d2b",
          border: "#1f2937",
        },
        brand: {
          red: "#e11d2e",       // cor de destaque / logo / crítico
        },
        severity: {
          critical: "#e11d2e",
          high: "#f97316",
          medium: "#eab308",
          low: "#22c55e",
        },
      },
      borderRadius: {
        xl: "14px",
      },
    },
  },
  plugins: [],
};

export default config;
