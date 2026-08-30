"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  FileText,
  Trash2,
  Search,
  MessageSquareText,
} from "lucide-react";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { TableSkeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { useToast } from "@/contexts/ToastContext";
import { apiClient, ApiError } from "@/lib/apiClient";
import type { Document, DocumentType } from "@/lib/types";
import { formatDate, cn } from "@/lib/utils";

interface RecentRunsTableProps {
  organizationId: string;
  refreshKey: number;
  onDeleted?: (documentId: string) => void;
  onUploadClick?: () => void;
}

const DOC_TYPE_LABELS: Record<DocumentType, string> = {
  security_questionnaire: "Security Questionnaire",
  invoice: "Invoice",
  compliance_log: "Compliance Log",
  other: "General Document",
};

const DOC_TYPE_BADGES: Record<DocumentType, string> = {
  security_questionnaire: "border-purple-500/20 bg-purple-500/10 text-purple-300",
  invoice: "border-emerald-500/20 bg-emerald-500/10 text-emerald-300",
  compliance_log: "border-blue-500/20 bg-blue-500/10 text-blue-300",
  other: "border-white/10 bg-white/5 text-white/60",
};

function displayName(document: Document): string {
  const fromPath = document.file_path.split("/").pop();
  return fromPath || DOC_TYPE_LABELS[document.doc_type];
}

export function RecentRunsTable({
  organizationId,
  refreshKey,
  onDeleted,
  onUploadClick,
}: RecentRunsTableProps) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const { showError, showSuccess } = useToast();

  useEffect(() => {
    if (!organizationId) return;

    let cancelled = false;

    async function loadDocuments() {
      setDocuments([]);
      setIsLoading(true);
      try {
        const result = await apiClient.get<Document[]>(
          `/documents/?organization=${organizationId}`
        );
        if (!cancelled) setDocuments(result);
      } catch {
        if (!cancelled) showError("Couldn't load recent document runs.");
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    loadDocuments();

    return () => {
      cancelled = true;
    };
  }, [organizationId, refreshKey, showError]);

  async function handleDelete(document: Document, e: React.MouseEvent) {
    e.stopPropagation();
    try {
      await apiClient.delete(`/documents/${document.id}/`);
      setDocuments((prev) => prev.filter((doc) => doc.id !== document.id));
      showSuccess(`Deleted "${displayName(document)}"`);
      onDeleted?.(document.id);
    } catch (error) {
      const message =
        error instanceof ApiError ? `delete failed (${error.status})` : "delete failed";
      showError(`Couldn't delete "${displayName(document)}" — ${message}.`);
    }
  }

  const filteredDocs = useMemo(() => {
    return documents.filter((doc) => {
      const nameMatch = displayName(doc).toLowerCase().includes(searchQuery.toLowerCase());
      const typeMatch = typeFilter === "all" || doc.doc_type === typeFilter;
      return nameMatch && typeMatch;
    });
  }, [documents, searchQuery, typeFilter]);

  if (!organizationId) return null;

  return (
    <div className="flex flex-col gap-3">
      {/* Table Header & Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold text-white/90">Recent Document Ingestion Runs</h2>
          <span className="rounded-full bg-white/[0.06] px-2 py-0.5 font-mono text-[11px] text-white/50 border border-white/[0.08]">
            {documents.length}
          </span>
        </div>

        {documents.length > 0 && (
          <div className="flex items-center gap-2">
            {/* Search Input */}
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-white/40" />
              <input
                type="text"
                placeholder="Filter runs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="h-8 rounded-lg border border-white/10 bg-white/[0.03] pl-8 pr-3 text-xs text-white placeholder-white/30 focus:border-indigo-400 focus:outline-none transition-all w-36 sm:w-48"
              />
            </div>

            {/* Type Filter */}
            <div className="relative">
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="h-8 rounded-lg border border-white/10 bg-[#16161c] px-2.5 text-xs text-white/70 focus:border-indigo-400 focus:outline-none cursor-pointer"
              >
                <option value="all">All Types</option>
                <option value="security_questionnaire">Security</option>
                <option value="invoice">Invoices</option>
                <option value="compliance_log">Compliance</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Table Card Container */}
      <div className="overflow-hidden rounded-2xl border border-white/[0.08] bg-[#111116]/80 backdrop-blur-xl shadow-xl">
        {isLoading && <TableSkeleton rows={4} />}

        {!isLoading && documents.length === 0 && (
          <div className="p-4">
            <EmptyState
              icon={<FileText className="h-6 w-6 text-indigo-400 stroke-[1.75]" />}
              title="No Document Ingestion Runs"
              description="Upload your first enterprise document (Security Questionnaire, Invoice, or Compliance Log) using the dropzone above to begin autonomous resolution."
              actionLabel="Drop Documents Above"
              onAction={onUploadClick}
            />
          </div>
        )}

        {!isLoading && documents.length > 0 && filteredDocs.length === 0 && (
          <div className="px-4 py-12 text-center text-xs text-white/40">
            No document runs match the filter &quot;{searchQuery}&quot;.
          </div>
        )}

        {!isLoading && filteredDocs.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-white/[0.08] bg-white/[0.02] text-[11px] font-medium text-white/40 uppercase tracking-wider">
                  <th className="px-4 py-3">Document</th>
                  <th className="px-4 py-3">Classification</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Timestamp</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {filteredDocs.map((document) => (
                  <tr
                    key={document.id}
                    className="group transition-colors hover:bg-white/[0.03]"
                  >
                    {/* Document Name */}
                    <td className="max-w-[14rem] truncate px-4 py-3 font-medium text-white/90">
                      <Link
                        href={`/dashboard/document/${document.id}`}
                        className="inline-flex items-center gap-2 hover:text-indigo-300 transition-colors"
                      >
                        <FileText className="h-3.5 w-3.5 text-indigo-400 shrink-0" />
                        <span className="truncate">{displayName(document)}</span>
                      </Link>
                    </td>

                    {/* Doc Type Badge */}
                    <td className="px-4 py-3">
                      <span
                        className={cn(
                          "inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-medium",
                          DOC_TYPE_BADGES[document.doc_type]
                        )}
                      >
                        {DOC_TYPE_LABELS[document.doc_type]}
                      </span>
                    </td>

                    {/* Status Badge */}
                    <td className="px-4 py-3">
                      <StatusBadge status={document.status} size="sm" />
                    </td>

                    {/* Created Date */}
                    <td className="px-4 py-3 text-white/40 font-mono text-[11px]">
                      {formatDate(document.created_at)}
                    </td>

                    {/* Quick Action Buttons */}
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1 opacity-80 group-hover:opacity-100 transition-opacity">
                        <Link
                          href={`/dashboard/document/${document.id}`}
                          className="flex h-7 w-7 items-center justify-center rounded-lg border border-white/5 bg-white/[0.03] text-white/50 hover:bg-indigo-500/20 hover:text-indigo-300 hover:border-indigo-500/30 transition-all"
                          title="Open Document Workbench"
                        >
                          <MessageSquareText className="h-3.5 w-3.5" />
                        </Link>

                        <button
                          type="button"
                          onClick={(e) => handleDelete(document, e)}
                          aria-label={`Delete ${displayName(document)}`}
                          title="Delete Document"
                          className="flex h-7 w-7 items-center justify-center rounded-lg border border-white/5 bg-white/[0.03] text-white/40 hover:bg-rose-500/20 hover:text-rose-300 hover:border-rose-500/30 transition-all"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
