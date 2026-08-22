export type DocumentType =
  | "security_questionnaire"
  | "invoice"
  | "compliance_log"
  | "other";

export type DocumentStatus = "pending" | "processing" | "completed" | "failed";

export interface DocumentUploadResponse {
  status: "processing";
  document_id: string;
}

export interface Document {
  id: string;
  organization: string;
  doc_type: DocumentType;
  status: DocumentStatus;
  file: string | null;
  file_path: string;
  latest_agent_run_id: string | null;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

export interface Answer {
  id: string;
  agent_run: string;
  question_text: string;
  content: string;
  executive_summary: string;
  risk_flags: string[];
  action_items: string[];
  confidence_score: number | null;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

export interface ToolCall {
  id: string;
  agent_run: string;
  tool_name: string;
  tool_input: unknown;
  tool_output: unknown;
  created_at: string;
}

export interface DocumentChunk {
  text: string;
  metadata?: Record<string, unknown>;
  distance?: number | null;
}

export interface ModelChatResult {
  model_name: string;
  provider: "groq" | "gemini" | string;
  response: string;
  execution_time_ms: number;
  status: "success" | "error";
  error?: string;
  is_simulated?: boolean;
}

export interface DocumentChatResponse {
  compare: boolean;
  question: string;
  retrieved_context: DocumentChunk[];
  results?: {
    groq: ModelChatResult;
    gemini: ModelChatResult;
    [key: string]: ModelChatResult;
  };
  result?: ModelChatResult;
  faster_model?: "groq" | "gemini" | string | null;
  time_diff_ms?: number | null;
}

export interface ChatMessage {
  id: string;
  sender: "user" | "assistant";
  question?: string;
  compare?: boolean;
  retrieved_context?: DocumentChunk[];
  results?: {
    groq: ModelChatResult;
    gemini: ModelChatResult;
  };
  result?: ModelChatResult;
  faster_model?: string | null;
  time_diff_ms?: number | null;
  timestamp: string;
  isPending?: boolean;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserProfile {
  id: string;
  user: number;
  username: string;
  email: string;
  organization: string;
  role: "admin" | "member" | "viewer";
  created_at: string;
  updated_at: string;
}

export interface HealthRule {
  id: string;
  organization: string;
  name: string;
  description: string;
  metric: string;
  threshold: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Playbook {
  id: string;
  organization: string;
  name: string;
  description: string;
  content: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuditLog {
  id: string;
  user_id: string | null;
  username: string | null;
  organization_id: string;
  action: "CREATE" | "UPDATE" | "DELETE" | string;
  resource_type: string;
  resource_id: string;
  timestamp: string;
  ip_address: string | null;
}

export interface AgentProfile {
  id: string;
  name: string;
  system_prompt: string;
  model_name: string;
  temperature: number;
  created_at: string;
  updated_at: string;
}

export interface AgentRun {
  id: string;
  document: string;
  document_name?: string;
  agent_profile: string;
  agent_profile_name?: string;
  status: "pending" | "running" | "succeeded" | "failed";
  started_at: string | null;
  finished_at: string | null;
  error_message: string;
  tool_calls_count?: number;
  created_at: string;
  updated_at: string;
}

export interface MCPToolInfo {
  name: string;
  description: string;
  server: string;
  input_schema: Record<string, unknown>;
  transport: string;
  status: string;
}

export interface SystemStatus {
  status: string;
  version: string;
  cluster: string;
  components: {
    supervisor_llm: {
      model: string;
      provider: string;
      configured: boolean;
      status: string;
    };
    worker_llm: {
      model: string;
      provider: string;
      configured: boolean;
      status: string;
    };
    vector_memory: {
      engine: string;
      embedding_model: string;
      cost_per_query: string;
      status: string;
    };
    cache_broker: {
      engine: string;
      ttl_seconds: number;
      status: string;
    };
    mcp_protocol: {
      version: string;
      server: string;
      tools_count: number;
      status: string;
    };
    security: {
      soc2_audit: string;
      rate_limiting: string;
      x_frame_options: string;
      nosniff: boolean;
    };
  };
}
