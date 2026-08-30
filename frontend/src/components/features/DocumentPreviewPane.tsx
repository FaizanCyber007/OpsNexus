import { FileText, ExternalLink, Eye } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";

interface DocumentPreviewPaneProps {
  fileUrl: string | null;
  fileName: string;
}

export function DocumentPreviewPane({ fileUrl, fileName }: DocumentPreviewPaneProps) {
  return (
    <Card className="flex h-full min-h-[26rem] flex-col p-0 overflow-hidden">
      {/* Pane Header */}
      <div className="flex items-center justify-between gap-3 border-b border-white/[0.08] bg-white/[0.02] px-5 py-3.5">
        <div className="flex items-center gap-2 min-w-0">
          <Eye className="h-4 w-4 text-indigo-400 shrink-0" />
          <span className="truncate text-xs font-semibold text-white/90">{fileName}</span>
        </div>

        {fileUrl && (
          <a
            href={fileUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 rounded-lg border border-indigo-500/20 bg-indigo-500/10 px-2.5 py-1 text-xs font-medium text-indigo-300 hover:bg-indigo-500/20 transition-colors"
          >
            <span>Open raw</span>
            <ExternalLink className="h-3 w-3" />
          </a>
        )}
      </div>

      {/* Pane Body Viewer */}
      <div className="flex-1 overflow-hidden bg-black/40">
        {fileUrl ? (
          <iframe
            src={fileUrl}
            title={fileName}
            sandbox="allow-scripts allow-same-origin"
            className="h-full min-h-[24rem] w-full border-none bg-[#181820]"
          />
        ) : (
          <div className="flex h-full min-h-[24rem] items-center justify-center p-6">
            <EmptyState
              icon={<FileText className="h-6 w-6 text-white/30" />}
              title="No File Attached"
              description="This document record does not have a raw binary file attached to display in the viewer."
            />
          </div>
        )}
      </div>
    </Card>
  );
}
