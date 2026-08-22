import { Sidebar } from "@/components/layout/Sidebar";
import { SettingsGovernanceContent } from "@/components/features/SettingsGovernanceContent";

export const metadata = {
  title: "Settings & Governance — OpsNexus",
  description: "Manage tenant organizations, health monitoring rules, operational playbooks, and infrastructure diagnostics.",
};

export default function SettingsPage() {
  return (
    <div className="flex h-screen w-full overflow-hidden bg-[#09090b]">
      <Sidebar />
      <main className="flex flex-1 flex-col overflow-y-auto p-6 sm:p-8">
        <SettingsGovernanceContent />
      </main>
    </div>
  );
}
