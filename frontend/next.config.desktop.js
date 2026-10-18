/**
 * Config usada SÓ pelo build desktop (desktop/build.bat).
 * A config normal (next.config.js) continua com output "standalone",
 * usada pelo modo Docker/servidor — não mexemos nela.
 *
 * "export" gera um site 100% estático (HTML/CSS/JS) em out/, sem precisar
 * de um processo Node rodando — o FastAPI do app desktop serve esses
 * arquivos direto (ver desktop/main.py).
 */

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "export",
  images: { unoptimized: true },
  trailingSlash: true, // garante que cada rota vire uma pasta com index.html (ex: /pentest/index.html)
};

module.exports = nextConfig;
