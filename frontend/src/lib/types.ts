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
