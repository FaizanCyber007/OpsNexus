import { Sidebar } from "@/components/layout/Sidebar";
import { DocumentsHubContent } from "@/components/features/DocumentsHubContent";

export const metadata = {
  title: "Documents Hub — OpsNexus",
  description: "Enterprise multi-tenant document repository, status tracking, and vector indexing.",
};

export default function DocumentsPage() {
  return (
    <div className="flex h-screen w-full overflow-hidden bg-[#09090b]">
      <Sidebar />
      <main className="flex flex-1 flex-col overflow-y-auto p-6 sm:p-8">
        <DocumentsHubContent />
      </main>
    </div>
  );
}
