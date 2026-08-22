import type {
  AgentProfile,
  AgentRun,
  Answer,
  AuditLog,
  Document,
  DocumentChatResponse,
  HealthRule,
  MCPToolInfo,
  Organization,
  Playbook,
  SystemStatus,
  ToolCall,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, body: unknown) {
    super(`API request failed with status ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const isFormData = init?.body instanceof FormData;

  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...init?.headers,
    },
  });

  if (!res.ok) {
    let body: unknown;
    try {
      body = await res.json();
    } catch {
      body = res.statusText;
    }
    throw new ApiError(res.status, body);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}

export const apiClient = {
  get: <T>(path: string) => request<T>(path, { method: "GET" }),
  post: <T>(path: string, data?: unknown) =>
    request<T>(path, {
      method: "POST",
      body:
        data instanceof FormData
          ? data
          : data !== undefined
            ? JSON.stringify(data)
            : undefined,
    }),
  patch: <T>(path: string, data?: unknown) =>
    request<T>(path, {
      method: "PATCH",
      body: data !== undefined ? JSON.stringify(data) : undefined,
    }),
  delete: <T = void>(path: string) => request<T>(path, { method: "DELETE" }),

  // Documents
  getDocuments: (orgId?: string) =>
    request<Document[]>(`/v1/documents/${orgId ? `?organization=${orgId}` : ""}`),
  getDocument: (id: string) => request<Document>(`/v1/documents/${id}/`),
  deleteDocument: (id: string) => request<void>(`/v1/documents/${id}/`, { method: "DELETE" }),
  getDocumentAnswers: (id: string) => request<Answer[]>(`/v1/documents/${id}/answers/`),
  chatDocument: (
    documentId: string,
    data: { question: string; compare?: boolean },
  ) =>
    request<DocumentChatResponse>(`/v1/documents/${documentId}/chat/`, {
      method: "POST",
      body: JSON.stringify(data),
      signal:
        typeof AbortSignal !== "undefined" && typeof AbortSignal.timeout === "function"
          ? AbortSignal.timeout(60000)
          : undefined,
    }),

  // Audit Logs
  getAuditLogs: (params?: { organization?: string; resource_type?: string; action?: string }) => {
    const query = new URLSearchParams();
    if (params?.organization) query.append("organization", params.organization);
    if (params?.resource_type) query.append("resource_type", params.resource_type);
    if (params?.action) query.append("action", params.action);
    const queryString = query.toString() ? `?${query.toString()}` : "";
    return request<AuditLog[]>(`/v1/audit-logs/${queryString}`);
  },

  // Health Rules
  getHealthRules: (orgId?: string) =>
    request<HealthRule[]>(`/v1/health-rules/${orgId ? `?organization=${orgId}` : ""}`),
  createHealthRule: (data: Partial<HealthRule>) =>
    request<HealthRule>("/v1/health-rules/", { method: "POST", body: JSON.stringify(data) }),
  updateHealthRule: (id: string, data: Partial<HealthRule>) =>
    request<HealthRule>(`/v1/health-rules/${id}/`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteHealthRule: (id: string) =>
    request<void>(`/v1/health-rules/${id}/`, { method: "DELETE" }),

  // Playbooks
  getPlaybooks: (orgId?: string) =>
    request<Playbook[]>(`/v1/playbooks/${orgId ? `?organization=${orgId}` : ""}`),
  createPlaybook: (data: Partial<Playbook>) =>
    request<Playbook>("/v1/playbooks/", { method: "POST", body: JSON.stringify(data) }),
  updatePlaybook: (id: string, data: Partial<Playbook>) =>
    request<Playbook>(`/v1/playbooks/${id}/`, { method: "PATCH", body: JSON.stringify(data) }),
  deletePlaybook: (id: string) =>
    request<void>(`/v1/playbooks/${id}/`, { method: "DELETE" }),

  // Organizations
  getOrganizations: () => request<Organization[]>("/v1/organizations/"),
  createOrganization: (data: Partial<Organization>) =>
    request<Organization>("/v1/organizations/", { method: "POST", body: JSON.stringify(data) }),

  // Agents & Swarm
  getAgentProfiles: () => request<AgentProfile[]>("/v1/agent-profiles/"),
  getAgentRuns: (params?: { document?: string; status?: string }) => {
    const query = new URLSearchParams();
    if (params?.document) query.append("document", params.document);
    if (params?.status) query.append("status", params.status);
    const queryString = query.toString() ? `?${query.toString()}` : "";
    return request<AgentRun[]>(`/v1/agent-runs/${queryString}`);
  },
  getAgentRun: (id: string) => request<AgentRun>(`/v1/agent-runs/${id}/`),
  getAgentToolCalls: (runId: string) =>
    request<ToolCall[]>(`/v1/agent-runs/${runId}/tool-calls/`),

  // System & MCP
  getSystemStatus: () => request<SystemStatus>("/v1/system/status/"),
  getMcpTools: () => request<{ tools: MCPToolInfo[]; server_version: string }>("/v1/mcp-tools/"),
  testMcpTool: (data: { tool_name: string; params?: Record<string, unknown>; organization_id?: string }) =>
    request<{ tool: string; status: string; result?: unknown; results?: unknown; results_count?: number }>(
      "/v1/mcp-tools/",
      { method: "POST", body: JSON.stringify(data) }
    ),
};
