import { Sidebar } from "@/components/layout/Sidebar";
import { DocumentDetailContent } from "@/components/features/DocumentDetailContent";

export default async function DocumentDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return (
    <div className="flex flex-1">
      <Sidebar />
      <DocumentDetailContent documentId={id} />
    </div>
  );
}
