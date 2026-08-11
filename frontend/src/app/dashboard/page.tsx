import { Sidebar } from "@/components/layout/Sidebar";
import { DocumentUploadCard } from "@/components/features/DocumentUploadCard";

export default function DashboardPage() {
  return (
    <div className="flex flex-1">
      <Sidebar />
      <main className="flex flex-1 items-center justify-center p-10">
        <DocumentUploadCard />
      </main>
    </div>
  );
}
