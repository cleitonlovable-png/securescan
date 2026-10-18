import VulnerabilitiesView from "@/components/VulnerabilitiesView";

export default function SecretsPage() {
  return (
    <VulnerabilitiesView
      title="Chaves e Secrets"
      subtitle="Chaves de API, tokens e credenciais encontrados expostos no código servido pela aplicação."
      category="secrets"
    />
  );
}
