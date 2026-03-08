import { DataTable } from "../components/data-table";
import { Card } from "../components/ui/card";
import { SectionTitle } from "../components/ui/section-title";
import { StatusPill } from "../components/ui/status-pill";
import { useDashboardData } from "../hooks/use-dashboard-data";
import { api } from "../lib/api";

export function SettingsPage() {
  const accounts = useDashboardData(api.exchangeAccounts, []);

  return (
    <div className="grid gap-6 xl:grid-cols-[1.35fr_1fr]">
      <Card>
        <SectionTitle
          eyebrow="Credential custody"
          title="Exchange accounts"
          description="Credentials are encrypted at rest and cannot be read back after write."
        />
        <DataTable
          rows={accounts.data}
          columns={[
            { key: "exchange", label: "Exchange", render: (item) => item.exchange },
            { key: "label", label: "Label", render: (item) => item.label },
            { key: "marketType", label: "Market type", render: (item) => item.marketType },
            {
              key: "rotation",
              label: "Last rotation",
              render: (item) => item.lastCredentialRotation,
            },
            {
              key: "status",
              label: "Status",
              render: (item) => (
                <StatusPill tone={item.status === "healthy" ? "positive" : "negative"}>
                  {item.status}
                </StatusPill>
              ),
            },
          ]}
        />
      </Card>
      <Card>
        <SectionTitle
          eyebrow="Secrets policy"
          title="Security guarantees"
          description="Backpack ED25519 material is treated as high-value and short-lived in memory."
        />
        <ul className="space-y-3 text-sm text-slate-300">
          <li>Application-layer encryption before PostgreSQL persistence.</li>
          <li>Audit log records who changed a credential, never the cleartext itself.</li>
          <li>Workers receive short-lived decrypted material only for active jobs.</li>
        </ul>
      </Card>
    </div>
  );
}
