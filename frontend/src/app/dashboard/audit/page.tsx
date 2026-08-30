import { Sidebar } from "@/components/layout/Sidebar";
import { AuditTrailContent } from "@/components/features/AuditTrailContent";

export const metadata = {
  title: "SOC2 Compliance & Audit Trail — OpsNexus",
  description: "Relational SOC2 audit trail, IP tracking, resource change monitoring, and compliance reporting.",
};

export default function AuditPage() {
  return (
    <div className="flex h-screen w-full overflow-hidden bg-[#09090b]">
      <Sidebar />
      <main className="flex flex-1 flex-col overflow-y-auto p-6 sm:p-8">
        <AuditTrailContent />
      </main>
    </div>
  );
}
