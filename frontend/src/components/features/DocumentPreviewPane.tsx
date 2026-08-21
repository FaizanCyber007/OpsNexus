import { Card } from "@/components/ui/Card";

interface DocumentPreviewPaneProps {
  fileUrl: string | null;
  fileName: string;
}

export function DocumentPreviewPane({ fileUrl, fileName }: DocumentPreviewPaneProps) {
  return (
    <Card className="flex h-full min-h-[24rem] flex-col p-0 lg:min-h-0">
      <div className="flex items-center justify-between gap-3 border-b border-white/10 px-4 py-3">
        <span className="truncate text-sm font-medium text-white/80">{fileName}</span>
        {fileUrl && (
          <a
            href={fileUrl}
            target="_blank"
            rel="noreferrer"
            className="shrink-0 text-xs font-medium text-indigo-300 hover:text-indigo-200"
          >
            Open raw file ↗
          </a>
        )}
      </div>

      <div className="flex-1 overflow-hidden rounded-b-2xl">
        {fileUrl ? (
          <iframe
            src={fileUrl}
            title={fileName}
            sandbox=""
            className="h-full min-h-[22rem] w-full bg-white/95"
          />
        ) : (
          <div className="flex h-full min-h-[22rem] items-center justify-center px-6 text-center text-sm text-white/40">
            No file attached to this document.
          </div>
        )}
      </div>
    </Card>
  );
}
