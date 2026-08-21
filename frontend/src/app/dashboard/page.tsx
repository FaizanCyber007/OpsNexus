import { Sidebar } from "@/components/layout/Sidebar";
import { DashboardContent } from "@/components/features/DashboardContent";

export default function DashboardPage() {
  return (
    <div className="flex flex-1 min-h-screen">
      <Sidebar />
      <main className="flex flex-1 justify-center overflow-y-auto p-6 sm:p-8 lg:p-10">
        <DashboardContent />
      </main>
    </div>
  );
}
