"use client";

import { useEffect, useState } from "react";

import { StatusBadge } from "@/components/ui/StatusBadge";
import { useToast } from "@/contexts/ToastContext";
import { apiClient, ApiError } from "@/lib/apiClient";
import type { Document, DocumentType } from "@/lib/types";

interface RecentRunsTableProps {
  organizationId: string;
  refreshKey: number;
}

const DOC_TYPE_LABELS: Record<DocumentType, string> = {
  security_questionnaire: "Security Questionnaire",
  invoice: "Invoice",
  compliance_log: "Compliance Log",
  other: "Other",
};

function displayName(document: Document): string {
  const fromPath = document.file_path.split("/").pop();
  return fromPath || DOC_TYPE_LABELS[document.doc_type];
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export function RecentRunsTable({ organizationId, refreshKey }: RecentRunsTableProps) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const { showError } = useToast();

  useEffect(() => {
    if (!organizationId) return;

    let cancelled = false;

    async function loadDocuments() {
      setIsLoading(true);
      try {
        const result = await apiClient.get<Document[]>(
          `/documents/?organization=${organizationId}`,
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

  async function handleDelete(document: Document) {
    try {
      await apiClient.delete(`/documents/${document.id}/`);
      setDocuments((prev) => prev.filter((doc) => doc.id !== document.id));
    } catch (error) {
      const message =
        error instanceof ApiError ? `delete failed (${error.status})` : "delete failed";
      showError(`Couldn't delete "${displayName(document)}" — ${message}.`);
    }
  }

  if (!organizationId) return null;

  return (
    <div className="flex flex-col gap-3">
      <h2 className="text-sm font-medium text-white/70">Recent Runs</h2>

      <div className="overflow-hidden rounded-xl border border-white/10 bg-white/5">
        {isLoading && documents.length === 0 && (
          <p className="px-4 py-6 text-center text-sm text-white/40">Loading…</p>
        )}

        {!isLoading && documents.length === 0 && (
          <p className="px-4 py-6 text-center text-sm text-white/40">
            No documents uploaded yet.
          </p>
        )}

        {documents.length > 0 && (
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-white/10 text-xs text-white/40">
                <th className="px-4 py-2.5 font-medium">Document</th>
                <th className="px-4 py-2.5 font-medium">Type</th>
                <th className="px-4 py-2.5 font-medium">Status</th>
                <th className="px-4 py-2.5 font-medium">Uploaded</th>
                <th className="px-4 py-2.5 font-medium" aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {documents.map((document) => (
                <tr
                  key={document.id}
                  className="border-b border-white/5 text-white/80 last:border-b-0 hover:bg-white/[0.03]"
                >
                  <td className="max-w-xs truncate px-4 py-2.5">{displayName(document)}</td>
                  <td className="px-4 py-2.5 text-white/60">
                    {DOC_TYPE_LABELS[document.doc_type]}
                  </td>
                  <td className="px-4 py-2.5">
                    <StatusBadge status={document.status} />
                  </td>
                  <td className="px-4 py-2.5 text-white/60">
                    {formatDate(document.created_at)}
                  </td>
                  <td className="px-4 py-2.5 text-right">
                    <button
                      type="button"
                      onClick={() => handleDelete(document)}
                      aria-label={`Delete ${displayName(document)}`}
                      className="text-white/40 transition-colors hover:text-status-critical"
                    >
                      <svg viewBox="0 0 16 16" className="h-4 w-4" fill="none">
                        <path
                          d="M3 4.5h10M6 4.5V3a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v1.5M6.5 7.5v4M9.5 7.5v4M4 4.5l.6 8.1a1 1 0 0 0 1 .9h4.8a1 1 0 0 0 1-.9l.6-8.1"
                          stroke="currentColor"
                          strokeWidth="1.3"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
