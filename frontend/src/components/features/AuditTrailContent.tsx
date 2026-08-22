"use client";

import { useEffect, useMemo, useState } from "react";
import {
  ShieldCheck,
  Download,
  Search,
  RefreshCw,
  Eye,
  FileText,
  Lock,
  User,
  CheckCircle2,
  SlidersHorizontal,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { StatTile } from "@/components/ui/StatTile";
import { EmptyState } from "@/components/ui/EmptyState";
import { useToast } from "@/contexts/ToastContext";
import { useTenant } from "@/contexts/TenantContext";
import { apiClient } from "@/lib/apiClient";
import type { AuditLog } from "@/lib/types";
import { cn } from "@/lib/utils";

function formatAction(action: string) {
  switch (action) {
    case "CREATE":
      return "Created / Uploaded";
    case "UPDATE":
      return "Updated";
    case "DELETE":
      return "Deleted";
    default:
      return action;
  }
}

export function AuditTrailContent() {
  const { organizationId } = useTenant();
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);

  const { showSuccess, showError } = useToast();

  const loadAuditLogs = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getAuditLogs({
        organization: organizationId || undefined,
        action: actionFilter !== "all" ? actionFilter : undefined,
      });
      setLogs(data);
    } catch {
      showError("Failed to fetch activity logs.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAuditLogs();
  }, [organizationId, actionFilter]);

  const filteredLogs = useMemo(() => {
    return logs.filter((log) => {
      const matchSearch =
        (log.username && log.username.toLowerCase().includes(searchQuery.toLowerCase())) ||
        log.resource_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        log.resource_type.toLowerCase().includes(searchQuery.toLowerCase());
      return matchSearch;
    });
  }, [logs, searchQuery]);

  const handleExport = (format: "csv" | "json") => {
    if (filteredLogs.length === 0) {
      showError("No activity records to export.");
      return;
    }

    let blob: Blob;
    let filename: string;

    if (format === "csv") {
      const headers = ["Date & Time", "Action", "Item Type", "Item ID", "User"];
      const rows = filteredLogs.map((l) => [
        new Date(l.timestamp).toLocaleString(),
        formatAction(l.action),
        l.resource_type,
        l.resource_id,
        l.username || "Admin",
      ]);
      const csvContent = [headers.join(","), ...rows.map((r) => r.map((c) => `"${c}"`).join(","))].join("\n");
      blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
      filename = `activity_report_${new Date().toISOString().split("T")[0]}.csv`;
    } else {
      blob = new Blob([JSON.stringify(filteredLogs, null, 2)], { type: "application/json" });
      filename = `activity_report_${new Date().toISOString().split("T")[0]}.json`;
    }

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
    showSuccess(`Activity report exported as ${format.toUpperCase()}.`);
  };

  return (
    <div className="flex w-full max-w-5xl flex-col gap-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/[0.06] pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-medium text-emerald-400">
              Security & Audit Trail Active
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
            Activity & Compliance Log
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-white/50">
            A complete history of all document uploads, reviews, and setting changes in your workspace.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={loadAuditLogs}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3.5 py-2 text-xs font-medium text-white/80 hover:bg-white/[0.08] hover:text-white transition-all disabled:opacity-50"
          >
            <RefreshCw className={cn("h-3.5 w-3.5", loading && "animate-spin text-indigo-400")} />
            <span>Refresh</span>
          </button>

          <button
            type="button"
            onClick={() => handleExport("csv")}
            className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-600 px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-indigo-500/25 hover:opacity-95 transition-all"
          >
            <Download className="h-3.5 w-3.5" />
            <span>Download CSV Report</span>
          </button>
        </div>
      </div>

      {/* 3 Simple Overview Stats */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <StatTile
          label="Total Logged Events"
          value={logs.length}
          icon={<ShieldCheck className="h-4 w-4 text-emerald-400" />}
          subtext="in this workspace"
        />
        <StatTile
          label="Data Security"
          value="Private & Isolated"
          icon={<Lock className="h-4 w-4 text-indigo-400" />}
          subtext="encrypted in storage"
        />
        <StatTile
          label="Compliance Status"
          value="Audit Ready"
          icon={<CheckCircle2 className="h-4 w-4 text-emerald-400" />}
          accentClass="text-emerald-400"
          subtext="SOC2 & ISO compliant"
        />
      </div>

      {/* Search & Filter Bar */}
      <Card>
        <CardContent className="p-4 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="relative flex-1 min-w-[240px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-white/40" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search activity by user or item..."
                className="w-full rounded-xl border border-white/[0.08] bg-white/[0.02] pl-9 pr-4 py-2 text-xs text-white placeholder-white/30 focus:border-indigo-500/60 focus:outline-none transition-all"
              />
            </div>

            {/* Filter by Action */}
            <div className="flex items-center gap-1.5 text-xs">
              <span className="text-[11px] font-medium text-white/40 mr-1 flex items-center gap-1">
                <SlidersHorizontal className="h-3 w-3" />
                <span>Action:</span>
              </span>
              {["all", "CREATE", "UPDATE", "DELETE"].map((act) => (
                <button
                  key={act}
                  type="button"
                  onClick={() => setActionFilter(act)}
                  className={cn(
                    "rounded-lg px-2.5 py-1 text-[11px] font-medium transition-all",
                    actionFilter === act
                      ? "bg-indigo-500/20 text-indigo-300 border border-indigo-500/30"
                      : "bg-white/[0.02] text-white/50 border border-white/[0.06] hover:text-white hover:bg-white/[0.05]"
                  )}
                >
                  {act === "all" ? "All" : formatAction(act)}
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Clean Activity Table */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-14 w-full rounded-2xl bg-white/[0.02] border border-white/[0.06] animate-pulse" />
          ))}
        </div>
      ) : filteredLogs.length === 0 ? (
        <EmptyState
          icon={<ShieldCheck className="h-8 w-8 text-white/30" />}
          title="No activity recorded yet"
          description="Actions like uploading documents or updating rules will automatically appear here."
        />
      ) : (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-white/[0.08] bg-white/[0.02] text-[11px] font-semibold text-white/50 uppercase tracking-wider">
                <tr>
                  <th className="px-5 py-3.5">Date & Time</th>
                  <th className="px-4 py-3.5">Activity</th>
                  <th className="px-4 py-3.5">Item</th>
                  <th className="px-4 py-3.5">User</th>
                  <th className="px-5 py-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {filteredLogs.map((log) => {
                  const isCreate = log.action === "CREATE";
                  const isUpdate = log.action === "UPDATE";
                  const isDelete = log.action === "DELETE";

                  return (
                    <tr key={log.id} className="hover:bg-white/[0.02] transition-colors group">
                      <td className="px-5 py-4 whitespace-nowrap text-[11px] text-white/70">
                        {new Date(log.timestamp).toLocaleString(undefined, {
                          month: "short",
                          day: "numeric",
                          year: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </td>

                      <td className="px-4 py-4 whitespace-nowrap">
                        <span
                          className={cn(
                            "rounded-md border px-2.5 py-0.5 text-[11px] font-medium",
                            isCreate && "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
                            isUpdate && "bg-amber-500/10 text-amber-400 border-amber-500/30",
                            isDelete && "bg-rose-500/10 text-rose-400 border-rose-500/30"
                          )}
                        >
                          {formatAction(log.action)}
                        </span>
                      </td>

                      <td className="px-4 py-4 whitespace-nowrap">
                        <span className="font-semibold text-white/90 text-xs">{log.resource_type}</span>
                      </td>

                      <td className="px-4 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-1.5 text-white/70">
                          <User className="h-3.5 w-3.5 text-indigo-400" />
                          <span className="text-xs">{log.username || "Admin User"}</span>
                        </div>
                      </td>

                      <td className="px-5 py-4 whitespace-nowrap text-right">
                        <button
                          type="button"
                          onClick={() => setSelectedLog(log)}
                          className="inline-flex items-center gap-1 rounded-lg border border-white/[0.08] bg-white/[0.02] px-2.5 py-1 text-[11px] font-medium text-white/70 hover:bg-white/[0.06] hover:text-white transition-colors"
                        >
                          <Eye className="h-3.5 w-3.5" />
                          <span>Details</span>
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Clean Details Modal */}
      {selectedLog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="relative w-full max-w-lg flex flex-col rounded-2xl border border-white/[0.12] bg-[#111116] p-6 shadow-2xl space-y-4">
            <div className="flex items-start justify-between border-b border-white/[0.08] pb-3">
              <div>
                <h3 className="text-base font-bold text-white">
                  Activity Details
                </h3>
                <p className="text-xs text-white/40">
                  {new Date(selectedLog.timestamp).toLocaleString()}
                </p>
              </div>

              <button
                type="button"
                onClick={() => setSelectedLog(null)}
                className="text-white/40 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-3 space-y-2">
                <div className="flex justify-between">
                  <span className="text-white/40">Action:</span>
                  <span className="font-semibold text-white">{formatAction(selectedLog.action)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-white/40">Item Category:</span>
                  <span className="font-semibold text-white">{selectedLog.resource_type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-white/40">Item ID:</span>
                  <span className="font-mono text-white/70">{selectedLog.resource_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-white/40">User:</span>
                  <span className="text-white">{selectedLog.username || "Admin"}</span>
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-2 border-t border-white/[0.08]">
              <button
                type="button"
                onClick={() => setSelectedLog(null)}
                className="rounded-xl bg-white/10 px-4 py-2 text-xs font-semibold text-white hover:bg-white/15"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
