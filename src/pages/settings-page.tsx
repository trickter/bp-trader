import { LoadingBlock, SectionState } from "../components/async-state";
import { DataTable } from "../components/data-table";
import { Card } from "../components/ui/card";
import { SectionTitle } from "../components/ui/section-title";
import { StatusPill } from "../components/ui/status-pill";
import { useDashboardData } from "../hooks/use-dashboard-data";
import { api } from "../lib/api";

export function SettingsPage() {
  const accounts = useDashboardData(api.exchangeAccounts, []);
  const agentContext = useDashboardData(api.agentContext, {
    mode: "admin",
    accountMode: "mock",
    availableCapabilities: [],
    capabilities: [],
    domainVocabulary: [],
    resources: {},
  });

  return (
    <div className="grid gap-6 xl:grid-cols-[1.35fr_1fr]">
      <Card>
        <SectionTitle
          eyebrow="Credential custody"
          title="Exchange accounts"
          description="Credentials are encrypted at rest and cannot be read back after write."
        />
        {accounts.loading ? (
          <LoadingBlock rows={3} />
        ) : accounts.error ? (
          <SectionState
            title="Exchange accounts failed to load"
            detail={accounts.error}
            tone="error"
          />
        ) : accounts.data.length === 0 ? (
          <SectionState
            title="No exchange accounts configured"
            detail="Add an encrypted Backpack credential set before enabling account-linked strategy runs."
          />
        ) : (
          <DataTable
            rows={accounts.data}
            getRowKey={(item) => item.id}
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
        )}
      </Card>
      <div className="space-y-6">
        <Card>
          <SectionTitle
            eyebrow="Secrets policy"
            title="Security guarantees"
            description="Backpack ED25519 material is treated as high-value and short-lived in memory."
          />
          <ul className="space-y-2 text-sm text-gray-600">
            <li className="rounded-xl border border-gray-100 bg-gray-50 px-4 py-3">Application-layer encryption before PostgreSQL persistence.</li>
            <li className="rounded-xl border border-gray-100 bg-gray-50 px-4 py-3">Audit log records who changed a credential, never the cleartext itself.</li>
            <li className="rounded-xl border border-gray-100 bg-gray-50 px-4 py-3">Workers receive short-lived decrypted material only for active jobs.</li>
          </ul>
        </Card>
        <Card>
          <SectionTitle
            eyebrow="Agent-native"
            title="Capability discovery"
            description="Read-only agent endpoints share the same normalized data surface the admin UI uses."
          />
          {agentContext.loading ? (
            <LoadingBlock rows={3} />
          ) : agentContext.error ? (
            <SectionState
              title="Agent context failed to load"
              detail={agentContext.error}
              tone="error"
            />
          ) : (
            <div className="space-y-2 text-sm text-gray-500">
              <div className="rounded-xl border border-gray-100 bg-gray-50 p-3.5">
                Account mode: <span className="font-semibold text-gray-900">{agentContext.data.accountMode}</span>
              </div>
              <div className="rounded-xl border border-gray-100 bg-gray-50 p-3.5">
                Capabilities: <span className="font-semibold text-gray-900">{agentContext.data.availableCapabilities.join(", ")}</span>
              </div>
              <div className="rounded-xl border border-gray-100 bg-gray-50 p-3.5">
                Vocabulary: <span className="font-semibold text-gray-900">{agentContext.data.domainVocabulary.join(", ")}</span>
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
