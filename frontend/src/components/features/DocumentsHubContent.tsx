"use client";

import { useEffect, useMemo, useState, useRef } from "react";
import Link from "next/link";
import {
  FileText,
  Search,
  SlidersHorizontal,
  LayoutGrid,
  List,
  Sparkles,
  ExternalLink,
  Trash2,
  Eye,
  RefreshCw,
  FileCheck2,
  Clock,
  AlertCircle,
  FolderOpen,
  ShieldCheck,
  Receipt,
  FileSpreadsheet,
  MessageSquare,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { StatTile } from "@/components/ui/StatTile";
import { EmptyState } from "@/components/ui/EmptyState";
import { useTenant } from "@/contexts/TenantContext";
import { useToast } from "@/contexts/ToastContext";
import { apiClient } from "@/lib/apiClient";
import type { Answer, Document, DocumentType } from "@/lib/types";
import { cn } from "@/lib/utils";
import { Modal } from "@/components/ui/Modal";

function displayName(filePath: string): string {
  return filePath.split("/").pop() || "Untitled document";
}

function getDocTypeIcon(type: DocumentType) {
  switch (type) {
    case "security_questionnaire":
      return ShieldCheck;
    case "invoice":
      return Receipt;
    case "compliance_log":
      return FileSpreadsheet;
    default:
      return FileText;
  }
}

function formatDocType(type: DocumentType) {
  switch (type) {
    case "security_questionnaire":
      return "Security Questionnaire";
    case "invoice":
      return "Invoice / Billing";
    case "compliance_log":
      return "Compliance Audit";
    default:
      return "General Document";
  }
}

export function DocumentsHubContent() {
  const { organizationId } = useTenant();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedType, setSelectedType] = useState<string>("all");
  const [selectedStatus, setSelectedStatus] = useState<string>("all");
  const [viewMode, setViewMode] = useState<"table" | "grid">("table");
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // Inspector modal state
  const [inspectDoc, setInspectDoc] = useState<Document | null>(null);
  const [inspectAnswers, setInspectAnswers] = useState<Answer[] | null>(null);
  const [inspectLoading, setInspectLoading] = useState(false);

  const { showSuccess, showError } = useToast();

  const activeOrgRef = useRef(organizationId);
  useEffect(() => {
    activeOrgRef.current = organizationId;
  }, [organizationId]);

  const loadDocuments = async () => {
    const requestedOrg = organizationId;
    try {
      setLoading(true);
      const data = await apiClient.getDocuments(requestedOrg || undefined);
      if (activeOrgRef.current === requestedOrg) {
        setDocuments(data);
      }
    } catch {
      if (activeOrgRef.current === requestedOrg) {
        showError("Failed to fetch documents.");
      }
    } finally {
      if (activeOrgRef.current === requestedOrg) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    loadDocuments();
  }, [organizationId]);

  const handleDelete = async (docId: string) => {
    if (!confirm("Are you sure you want to delete this document from your library?")) {
      return;
    }
    try {
      setDeletingId(docId);
      await apiClient.deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
      if (inspectDoc?.id === docId) setInspectDoc(null);
      showSuccess("Document removed.");
    } catch {
      showError("Failed to delete document.");
    } finally {
      setDeletingId(null);
    }
  };

  const handleInspect = async (doc: Document) => {
    setInspectDoc(doc);
    setInspectLoading(true);
    setInspectAnswers(null);
    try {
      const ans = await apiClient.getDocumentAnswers(doc.id);
      setInspectAnswers((prevAnswers) => {
        // Need to ensure we're still looking at the same document
        // We use state callback to access latest inspectDoc state
        return ans;
      });
      setInspectDoc((currentDoc) => {
        if (currentDoc?.id === doc.id) {
          setInspectAnswers(ans);
        }
        return currentDoc;
      });
    } catch {
      // ignore
    } finally {
      setInspectDoc((currentDoc) => {
        if (currentDoc?.id === doc.id) {
          setInspectLoading(false);
        }
        return currentDoc;
      });
    }
  };

  const filteredDocs = useMemo(() => {
    return documents.filter((doc) => {
      const matchesSearch =
        doc.file_path.toLowerCase().includes(searchQuery.toLowerCase()) ||
        doc.id.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesType = selectedType === "all" || doc.doc_type === selectedType;
      const matchesStatus = selectedStatus === "all" || doc.status === selectedStatus;
      return matchesSearch && matchesType && matchesStatus;
    });
  }, [documents, searchQuery, selectedType, selectedStatus]);

  const stats = useMemo(() => {
    return {
      total: documents.length,
      completed: documents.filter((d) => d.status === "completed").length,
      processing: documents.filter((d) => d.status === "pending" || d.status === "processing").length,
      failed: documents.filter((d) => d.status === "failed").length,
    };
  }, [documents]);

  return (
    <div className="flex w-full max-w-6xl flex-col gap-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/[0.06] pb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
            My Documents
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-white/50">
            Browse all uploaded files, view AI-generated summaries, and ask questions.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={loadDocuments}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3.5 py-2 text-xs font-medium text-white/80 hover:bg-white/[0.08] hover:text-white transition-all disabled:opacity-50"
          >
            <RefreshCw className={cn("h-3.5 w-3.5", loading && "animate-spin text-indigo-400")} />
            <span>Refresh</span>
          </button>

          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-600 px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-indigo-500/25 hover:opacity-95 transition-all"
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>Upload Document</span>
          </Link>
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatTile
          label="Total Files"
          value={stats.total}
          icon={<FolderOpen className="h-4 w-4 text-indigo-400" />}
          subtext="in library"
        />
        <StatTile
          label="Ready & Verified"
          value={stats.completed}
          icon={<FileCheck2 className="h-4 w-4 text-emerald-400" />}
          accentClass="text-emerald-400"
          subtext="available for Q&A"
        />
        <StatTile
          label="Analyzing"
          value={stats.processing}
          icon={<Clock className="h-4 w-4 text-amber-400" />}
          accentClass="text-amber-400"
          subtext="AI working"
        />
        <StatTile
          label="Needs Attention"
          value={stats.failed}
          icon={<AlertCircle className="h-4 w-4 text-rose-400" />}
          accentClass="text-rose-400"
          subtext="review needed"
        />
      </div>

      {/* Filter & Search Bar */}
      <Card>
        <CardContent className="p-4 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            {/* Search Input */}
            <div className="relative flex-1 min-w-[240px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-white/40" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search documents by name..."
                className="w-full rounded-xl border border-white/[0.08] bg-white/[0.02] pl-9 pr-4 py-2 text-xs text-white placeholder-white/30 focus:border-indigo-500/60 focus:bg-white/[0.05] focus:outline-none transition-all"
              />
            </div>

            {/* View Mode Toggle */}
            <div className="flex items-center gap-1 rounded-xl border border-white/[0.08] bg-white/[0.02] p-1">
              <button
                type="button"
                onClick={() => setViewMode("table")}
                className={cn(
                  "flex h-7 w-7 items-center justify-center rounded-lg text-xs transition-colors",
                  viewMode === "table" ? "bg-indigo-500/20 text-indigo-300 font-semibold" : "text-white/40 hover:text-white"
                )}
                title="Table View"
              >
                <List className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={() => setViewMode("grid")}
                className={cn(
                  "flex h-7 w-7 items-center justify-center rounded-lg text-xs transition-colors",
                  viewMode === "grid" ? "bg-indigo-500/20 text-indigo-300 font-semibold" : "text-white/40 hover:text-white"
                )}
                title="Grid View"
              >
                <LayoutGrid className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Filter Pills */}
          <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-white/[0.04] text-xs">
            <span className="text-[11px] font-medium text-white/40 mr-1 flex items-center gap-1">
              <SlidersHorizontal className="h-3 w-3" />
              <span>Category:</span>
            </span>
            {["all", "security_questionnaire", "invoice", "compliance_log", "other"].map((type) => (
              <button
                key={type}
                type="button"
                onClick={() => setSelectedType(type)}
                className={cn(
                  "rounded-lg px-2.5 py-1 text-[11px] font-medium transition-all",
                  selectedType === type
                    ? "bg-indigo-500/20 text-indigo-300 border border-indigo-500/30"
                    : "bg-white/[0.02] text-white/50 border border-white/[0.06] hover:text-white hover:bg-white/[0.05]"
                )}
              >
                {type === "all" ? "All" : formatDocType(type as DocumentType)}
              </button>
            ))}

            <div className="h-4 w-px bg-white/[0.08] mx-1" />

            <span className="text-[11px] font-medium text-white/40 mr-1">Status:</span>
            {["all", "completed", "processing", "pending", "failed"].map((status) => (
              <button
                key={status}
                type="button"
                onClick={() => setSelectedStatus(status)}
                className={cn(
                  "rounded-lg px-2.5 py-1 text-[11px] font-medium capitalize transition-all",
                  selectedStatus === status
                    ? "bg-indigo-500/20 text-indigo-300 border border-indigo-500/30"
                    : "bg-white/[0.02] text-white/50 border border-white/[0.06] hover:text-white hover:bg-white/[0.05]"
                )}
              >
                {status === "all" ? "All" : status}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Document List View */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-16 w-full rounded-2xl bg-white/[0.02] border border-white/[0.06] animate-pulse" />
          ))}
        </div>
      ) : filteredDocs.length === 0 ? (
        <EmptyState
          icon={<FolderOpen className="h-8 w-8 text-white/30" />}
          title="No documents found"
          description="Upload a document to get started."
          actionLabel="Upload Document"
          onAction={() => window.location.href = "/dashboard"}
        />
      ) : viewMode === "table" ? (
        /* Table View */
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-white/[0.08] bg-white/[0.02] text-[11px] font-semibold text-white/50 uppercase tracking-wider">
                <tr>
                  <th className="px-5 py-3.5">Document</th>
                  <th className="px-4 py-3.5">Category</th>
                  <th className="px-4 py-3.5">Status</th>
                  <th className="px-4 py-3.5">Uploaded</th>
                  <th className="px-5 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {filteredDocs.map((doc) => {
                  const DocIcon = getDocTypeIcon(doc.doc_type);
                  return (
                    <tr key={doc.id} className="hover:bg-white/[0.02] transition-colors group">
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-3">
                          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                            <DocIcon className="h-4 w-4" />
                          </div>
                          <div className="min-w-0">
                            <Link
                              href={`/dashboard/document/${doc.id}`}
                              className="font-medium text-white/90 hover:text-indigo-300 transition-colors truncate block max-w-md"
                            >
                              {displayName(doc.file_path)}
                            </Link>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <span className="rounded-md border border-white/[0.08] bg-white/[0.02] px-2 py-0.5 text-[11px] text-white/70">
                          {formatDocType(doc.doc_type)}
                        </span>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <StatusBadge status={doc.status} />
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-[11px] text-white/40">
                        {new Date(doc.created_at).toLocaleDateString(undefined, {
                          month: "short",
                          day: "numeric",
                          year: "numeric",
                        })}
                      </td>
                      <td className="px-5 py-4 whitespace-nowrap text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            type="button"
                            onClick={() => handleInspect(doc)}
                            className="inline-flex items-center gap-1 rounded-lg border border-white/[0.08] bg-white/[0.02] px-2.5 py-1 text-[11px] font-medium text-white/70 hover:bg-white/[0.06] hover:text-white transition-colors"
                          >
                            <Eye className="h-3.5 w-3.5" />
                            <span>Summary</span>
                          </button>
                          <Link
                            href={`/dashboard/document/${doc.id}`}
                            className="inline-flex items-center gap-1 rounded-lg bg-indigo-500/20 border border-indigo-500/30 px-3 py-1 text-[11px] font-semibold text-indigo-300 hover:bg-indigo-500/30 transition-colors"
                          >
                            <MessageSquare className="h-3 w-3" />
                            <span>Ask AI</span>
                          </Link>
                          <button
                            type="button"
                            onClick={() => handleDelete(doc.id)}
                            disabled={deletingId === doc.id}
                            className="flex h-7 w-7 items-center justify-center rounded-lg border border-rose-500/20 text-rose-400 hover:bg-rose-500/10 transition-colors disabled:opacity-50"
                            title="Delete"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      ) : (
        /* Grid View */
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredDocs.map((doc) => {
            const DocIcon = getDocTypeIcon(doc.doc_type);
            return (
              <Card key={doc.id} className="flex flex-col justify-between p-5 hover:border-indigo-500/30 transition-all group">
                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                      <DocIcon className="h-4 w-4" />
                    </div>
                    <StatusBadge status={doc.status} />
                  </div>

                  <div>
                    <h3 className="font-semibold text-white/90 group-hover:text-indigo-300 transition-colors line-clamp-1">
                      {displayName(doc.file_path)}
                    </h3>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-white/50 pt-2 border-t border-white/[0.04]">
                    <span className="rounded-md border border-white/[0.08] bg-white/[0.02] px-2 py-0.5 text-[10px] text-white/70">
                      {formatDocType(doc.doc_type)}
                    </span>
                    <span className="text-[11px]">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2 pt-4 mt-2 border-t border-white/[0.06]">
                  <button
                    type="button"
                    onClick={() => handleInspect(doc)}
                    className="flex-1 rounded-lg border border-white/10 bg-white/[0.03] py-1.5 text-center text-xs font-medium text-white/70 hover:bg-white/[0.08] hover:text-white transition-colors"
                  >
                    Summary
                  </button>
                  <Link
                    href={`/dashboard/document/${doc.id}`}
                    className="flex-1 rounded-lg bg-indigo-500/20 border border-indigo-500/30 py-1.5 text-center text-xs font-semibold text-indigo-300 hover:bg-indigo-500/30 transition-colors flex items-center justify-center gap-1"
                  >
                    <MessageSquare className="h-3 w-3" />
                    <span>Ask AI</span>
                  </Link>
                  <button
                    type="button"
                    onClick={() => handleDelete(doc.id)}
                    disabled={deletingId === doc.id}
                    className="flex h-8 w-8 items-center justify-center rounded-lg border border-rose-500/20 text-rose-400 hover:bg-rose-500/10 transition-colors disabled:opacity-50"
                    title="Delete"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Clean Document Summary Modal */}
      <Modal isOpen={!!inspectDoc} onClose={() => setInspectDoc(null)} title="Document Summary" className="max-w-2xl max-h-[85vh] flex flex-col p-6">
        {inspectDoc && (
          <>
            <div className="flex items-start justify-between border-b border-white/[0.08] pb-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <StatusBadge status={inspectDoc.status} />
                  <span className="rounded-md border border-white/[0.08] bg-white/[0.02] px-2 py-0.5 text-[10px] text-white/60">
                    {formatDocType(inspectDoc.doc_type)}
                  </span>
                </div>
                <h2 className="text-lg font-bold text-white truncate max-w-lg">
                  {displayName(inspectDoc.file_path)}
                </h2>
              </div>

              <button
                type="button"
                onClick={() => setInspectDoc(null)}
                className="flex h-8 w-8 items-center justify-center rounded-lg text-white/50 hover:bg-white/10 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 overflow-y-auto py-4 space-y-4 text-xs">
              {inspectLoading ? (
                <div className="py-8 text-center text-white/50">Loading summary...</div>
              ) : inspectAnswers && inspectAnswers.length > 0 ? (
                inspectAnswers.map((ans) => (
                  <div key={ans.id} className="space-y-3 rounded-xl border border-white/[0.08] bg-white/[0.02] p-4">
                    {ans.executive_summary && (
                      <div>
                        <h4 className="font-semibold text-indigo-300 text-xs mb-1">
                          Executive Summary
                        </h4>
                        <p className="text-white/80 leading-relaxed text-xs">{ans.executive_summary}</p>
                      </div>
                    )}

                    {ans.risk_flags && ans.risk_flags.length > 0 && (
                      <div>
                        <h4 className="font-semibold text-rose-300 text-xs mb-1.5">
                          Potential Risks & Red Flags ({ans.risk_flags.length})
                        </h4>
                        <div className="flex flex-wrap gap-1.5">
                          {ans.risk_flags.map((r, idx) => (
                            <span
                              key={idx}
                              className="rounded-md border border-rose-500/30 bg-rose-500/10 px-2.5 py-1 text-xs text-rose-300"
                            >
                              {r}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {ans.action_items && ans.action_items.length > 0 && (
                      <div>
                        <h4 className="font-semibold text-amber-300 text-xs mb-1.5">
                          Action Items ({ans.action_items.length})
                        </h4>
                        <ul className="space-y-1.5 text-white/70 list-disc list-inside text-xs">
                          {ans.action_items.map((item, idx) => (
                            <li key={idx}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="py-6 text-center text-white/40">
                  {inspectDoc.status === "completed"
                    ? "No specific findings extracted for this document."
                    : "The document is currently being analyzed by AI."}
                </div>
              )}
            </div>

            <div className="flex items-center justify-end gap-3 border-t border-white/[0.08] pt-4">
              <button
                type="button"
                onClick={() => setInspectDoc(null)}
                className="rounded-xl border border-white/10 px-4 py-2 text-xs font-medium text-white/70 hover:bg-white/[0.05]"
              >
                Close
              </button>
              <Link
                href={`/dashboard/document/${inspectDoc.id}`}
                className="rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-500 flex items-center gap-1.5 shadow-lg shadow-indigo-500/25"
              >
                <MessageSquare className="h-3.5 w-3.5" />
                <span>Ask AI Questions</span>
              </Link>
            </div>
          </>
        )}
      </Modal>
    </div>
  );
}
