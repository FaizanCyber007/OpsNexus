"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { Card } from "@/components/ui/Card";
import { Shimmer } from "@/components/ui/Shimmer";
import { useToast } from "@/contexts/ToastContext";
import { apiClient } from "@/lib/apiClient";
import type { ChatMessage, Document, DocumentChunk } from "@/lib/types";

interface DocumentChatPanelProps {
  document: Document | null;
  documentId: string;
}

const PROMPT_SUGGESTIONS = [
  {
    icon: "🔍",
    label: "Key Risks & Liabilities",
    prompt: "What are the primary risk factors, liabilities, or red flags identified in this document?",
  },
  {
    icon: "💰",
    label: "Payment & Commercial Terms",
    prompt: "What are the payment terms, billing cycles, pricing, or financial penalties specified?",
  },
  {
    icon: "🔒",
    label: "Security & Compliance Clauses",
    prompt: "Are there any specific security, data privacy (GDPR/SOC2), or compliance requirements mentioned?",
  },
  {
    icon: "📋",
    label: "Action Items & Deliverables",
    prompt: "List all concrete action items, deliverables, and deadlines required by this document.",
  },
];

function ContextSnippetsDisclosure({ chunks }: { chunks: DocumentChunk[] }) {
  const [isOpen, setIsOpen] = useState(false);

  if (!chunks || chunks.length === 0) return null;

  return (
    <div className="mt-3 border-t border-white/10 pt-2.5">
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="inline-flex items-center gap-1.5 text-xs font-medium text-indigo-300 hover:text-indigo-200 transition-colors"
      >
        <span>{isOpen ? "Hide ChromaDB Context ▲" : `View ${chunks.length} ChromaDB Context Chunk(s) ▼`}</span>
      </button>

      {isOpen && (
        <div className="mt-2.5 flex flex-col gap-2 rounded-lg bg-black/40 p-3 border border-white/5 text-xs">
          {chunks.map((chunk, idx) => (
            <div key={idx} className="flex flex-col gap-1 border-b border-white/5 pb-2 last:border-b-0 last:pb-0">
              <div className="flex items-center justify-between text-[11px] text-white/40">
                <span className="font-mono">Chunk #{idx + 1}</span>
                {chunk.distance != null && (
                  <span className="text-white/30">Distance: {chunk.distance.toFixed(3)}</span>
                )}
              </div>
              <p className="whitespace-pre-wrap leading-relaxed text-white/70 font-mono text-[11px]">
                {chunk.text}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function DocumentChatPanel({ document, documentId }: DocumentChatPanelProps) {
  const [isArenaMode, setIsArenaMode] = useState(true);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { showError, showToast } = useToast();
  const chatBottomRef = useRef<HTMLDivElement>(null);
  const messageCounter = useRef(0);

  const scrollToBottom = useCallback(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isSubmitting, scrollToBottom]);

  const handleSendMessage = async (queryText: string) => {
    const question = queryText.trim();
    if (!question || isSubmitting) return;

    setInputQuery("");
    const userMsgId = `user-msg-${messageCounter.current++}`;
    const assistantMsgId = `assistant-msg-${messageCounter.current++}`;

    const userMessage: ChatMessage = {
      id: userMsgId,
      sender: "user",
      question,
      timestamp: "Just now",
    };

    const pendingAssistantMessage: ChatMessage = {
      id: assistantMsgId,
      sender: "assistant",
      question,
      compare: isArenaMode,
      isPending: true,
      timestamp: "Just now",
    };

    setMessages((prev) => [...prev, userMessage, pendingAssistantMessage]);
    setIsSubmitting(true);

    try {
      const response = await apiClient.chatDocument(documentId, {
        question,
        compare: isArenaMode,
      });

      setMessages((prev) =>
        prev.map((msg) => {
          if (msg.id === assistantMsgId) {
            return {
              ...msg,
              isPending: false,
              compare: response.compare,
              retrieved_context: response.retrieved_context,
              results: response.results ? {
                groq: response.results.groq,
                gemini: response.results.gemini,
              } : undefined,
              result: response.result,
              faster_model: response.faster_model,
              time_diff_ms: response.time_diff_ms,
            };
          }
          return msg;
        })
      );
    } catch (err) {
      setMessages((prev) => prev.filter((msg) => msg.id !== assistantMsgId));
      showError("Chat query failed or timed out. Please check your connection and retry.");
      console.error("Document chat error:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
    showToast("Chat history cleared.", "info");
  };

  return (
    <Card className="flex h-full min-h-[30rem] flex-col overflow-hidden p-0">
      {/* Top Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 bg-white/[0.02] px-5 py-3.5">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/20 text-indigo-300 font-mono text-xs">
            💬
          </div>
          <div>
            <h2 className="text-sm font-semibold text-white">Document RAG Chat</h2>
            <p className="text-[11px] text-white/40">
              ChromaDB semantic retrieval & real-time inference
            </p>
          </div>
        </div>

        {/* Model Arena Switch Toggle */}
        <div className="flex items-center gap-3">
          {messages.length > 0 && (
            <button
              type="button"
              onClick={clearChat}
              disabled={isSubmitting}
              className="text-xs text-white/40 hover:text-white/70 transition-colors disabled:opacity-40"
              title="Clear conversation"
            >
              Clear
            </button>
          )}

          <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5">
            <span className="text-xs font-medium text-white/70 flex items-center gap-1">
              ⚔️ <span className="hidden sm:inline">Model Arena</span>
            </span>
            <button
              type="button"
              role="switch"
              aria-checked={isArenaMode}
              onClick={() => setIsArenaMode((prev) => !prev)}
              className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                isArenaMode ? "bg-indigo-600" : "bg-white/20"
              }`}
            >
              <span
                aria-hidden="true"
                className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                  isArenaMode ? "translate-x-4" : "translate-x-0"
                }`}
              />
            </button>
          </div>
        </div>
      </div>

      {/* Model Mode Banner */}
      <div className="border-b border-white/5 bg-white/[0.01] px-5 py-2 text-xs flex items-center justify-between text-white/50">
        <div className="flex items-center gap-2">
          {isArenaMode ? (
            <>
              <span className="inline-flex items-center gap-1 rounded bg-amber-500/10 px-2 py-0.5 text-[11px] font-medium text-amber-300 border border-amber-500/20">
                ⚡ Arena Mode
              </span>
              <span>Comparing <strong>Groq (Llama-3 70B)</strong> vs <strong>Gemini Flash</strong> simultaneously</span>
            </>
          ) : (
            <>
              <span className="inline-flex items-center gap-1 rounded bg-blue-500/10 px-2 py-0.5 text-[11px] font-medium text-blue-300 border border-blue-500/20">
                Single Model
              </span>
              <span>Standard Gemini Flash generation</span>
            </>
          )}
        </div>
        {document?.status === "processing" && (
          <span className="text-[11px] text-amber-300/80 animate-pulse">
            Ingestion in progress…
          </span>
        )}
      </div>

      {/* Chat Messages Stream */}
      <div className="flex-1 overflow-y-auto p-5 space-y-6">
        {messages.length === 0 ? (
          /* Empty State */
          <div className="flex flex-col items-center justify-center py-8 px-4 text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-white/10 shadow-lg text-2xl mb-4">
              ⚔️
            </div>
            <h3 className="text-base font-medium text-white mb-1">
              Ask anything about this document
            </h3>
            <p className="text-xs text-white/50 max-w-md mb-6 leading-relaxed">
              Vector chunks from ChromaDB will be retrieved and synthesized live. Toggle <strong>Model Arena</strong> to benchmark Groq (Llama-3 70B) against Gemini Flash side-by-side!
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full max-w-xl">
              {PROMPT_SUGGESTIONS.map((item, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSendMessage(item.prompt)}
                  disabled={isSubmitting}
                  className="flex items-start gap-2.5 rounded-xl border border-white/10 bg-white/5 p-3 text-left transition-all hover:bg-white/10 hover:border-white/20 active:scale-[0.98] disabled:opacity-50"
                >
                  <span className="text-lg shrink-0 mt-0.5">{item.icon}</span>
                  <div>
                    <div className="text-xs font-medium text-white/90">{item.label}</div>
                    <div className="text-[11px] text-white/40 line-clamp-1 mt-0.5">
                      {item.prompt}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className="space-y-4">
              {/* User Message */}
              {msg.sender === "user" && (
                <div className="flex justify-end">
                  <div className="max-w-[85%] rounded-2xl bg-gradient-to-r from-indigo-600 to-violet-600 px-4 py-3 text-sm text-white shadow-lg">
                    <div className="flex items-center justify-between gap-3 mb-1 text-[11px] text-white/70">
                      <span className="font-semibold">You</span>
                      <span>{msg.timestamp}</span>
                    </div>
                    <p className="whitespace-pre-wrap leading-relaxed">{msg.question}</p>
                  </div>
                </div>
              )}

              {/* Assistant Message */}
              {msg.sender === "assistant" && (
                <div className="space-y-3">
                  {msg.compare ? (
                    /* Arena Side-by-Side View */
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                      {/* Groq Column */}
                      <div className="flex flex-col rounded-xl border border-amber-500/20 bg-amber-950/10 p-4 shadow-md transition-all">
                        <div className="flex items-center justify-between border-b border-amber-500/10 pb-2.5 mb-3">
                          <div className="flex items-center gap-2">
                            <span className="flex h-5 w-5 items-center justify-center rounded bg-amber-500/20 text-amber-300 text-xs font-bold">
                              ⚡
                            </span>
                            <span className="text-xs font-semibold text-amber-200">
                              Groq (Llama-3 70B)
                            </span>
                          </div>

                          <div className="flex items-center gap-1.5">
                            {msg.faster_model === "groq" && msg.time_diff_ms != null && (
                              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/20 border border-emerald-500/40 px-2 py-0.5 text-[10px] font-semibold text-emerald-300 animate-pulse">
                                🏆 Faster by {msg.time_diff_ms}ms
                              </span>
                            )}
                            {msg.results?.groq?.execution_time_ms !== undefined && (
                              <span className="rounded bg-white/10 px-2 py-0.5 font-mono text-[11px] text-white/70">
                                {msg.results.groq.execution_time_ms}ms
                              </span>
                            )}
                          </div>
                        </div>

                        {msg.isPending ? (
                          <div className="space-y-2.5 py-1">
                            <Shimmer className="h-3.5 w-3/4 bg-amber-500/10" />
                            <Shimmer className="h-3.5 w-full bg-amber-500/10" />
                            <Shimmer className="h-3.5 w-5/6 bg-amber-500/10" />
                            <Shimmer className="h-3.5 w-2/3 bg-amber-500/10" />
                          </div>
                        ) : (
                          <div className="text-xs leading-relaxed text-white/90 whitespace-pre-wrap flex-1">
                            {msg.results?.groq?.response || "No response received."}
                          </div>
                        )}
                      </div>

                      {/* Gemini Flash Column */}
                      <div className="flex flex-col rounded-xl border border-indigo-500/20 bg-indigo-950/10 p-4 shadow-md transition-all">
                        <div className="flex items-center justify-between border-b border-indigo-500/10 pb-2.5 mb-3">
                          <div className="flex items-center gap-2">
                            <span className="flex h-5 w-5 items-center justify-center rounded bg-indigo-500/20 text-indigo-300 text-xs font-bold">
                              ✨
                            </span>
                            <span className="text-xs font-semibold text-indigo-200">
                              Gemini Flash
                            </span>
                          </div>

                          <div className="flex items-center gap-1.5">
                            {msg.faster_model === "gemini" && msg.time_diff_ms != null && (
                              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/20 border border-emerald-500/40 px-2 py-0.5 text-[10px] font-semibold text-emerald-300 animate-pulse">
                                🏆 Faster by {msg.time_diff_ms}ms
                              </span>
                            )}
                            {msg.results?.gemini?.execution_time_ms !== undefined && (
                              <span className="rounded bg-white/10 px-2 py-0.5 font-mono text-[11px] text-white/70">
                                {msg.results.gemini.execution_time_ms}ms
                              </span>
                            )}
                          </div>
                        </div>

                        {msg.isPending ? (
                          <div className="space-y-2.5 py-1">
                            <Shimmer className="h-3.5 w-4/5 bg-indigo-500/10" />
                            <Shimmer className="h-3.5 w-full bg-indigo-500/10" />
                            <Shimmer className="h-3.5 w-11/12 bg-indigo-500/10" />
                            <Shimmer className="h-3.5 w-3/5 bg-indigo-500/10" />
                          </div>
                        ) : (
                          <div className="text-xs leading-relaxed text-white/90 whitespace-pre-wrap flex-1">
                            {msg.results?.gemini?.response || "No response received."}
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    /* Single Model View */
                    <div className="rounded-xl border border-white/10 bg-white/5 p-4 shadow-md">
                      <div className="flex items-center justify-between border-b border-white/10 pb-2 mb-3">
                        <div className="flex items-center gap-2">
                          <span className="flex h-5 w-5 items-center justify-center rounded bg-indigo-500/20 text-indigo-300 text-xs">
                            🤖
                          </span>
                          <span className="text-xs font-semibold text-white/90">
                            {msg.result?.model_name || "AI Assistant"}
                          </span>
                        </div>
                        {msg.result?.execution_time_ms !== undefined && (
                          <span className="rounded bg-white/10 px-2 py-0.5 font-mono text-[11px] text-white/70">
                            {msg.result.execution_time_ms}ms
                          </span>
                        )}
                      </div>

                      {msg.isPending ? (
                        <div className="space-y-2.5 py-1">
                          <Shimmer className="h-3.5 w-2/3" />
                          <Shimmer className="h-3.5 w-full" />
                          <Shimmer className="h-3.5 w-5/6" />
                        </div>
                      ) : (
                        <div className="text-xs leading-relaxed text-white/90 whitespace-pre-wrap">
                          {msg.result?.response || "No response."}
                        </div>
                      )}
                    </div>
                  )}

                  {/* ChromaDB Context Citations Dropdown */}
                  {!msg.isPending && msg.retrieved_context && (
                    <ContextSnippetsDisclosure chunks={msg.retrieved_context} />
                  )}
                </div>
              )}
            </div>
          ))
        )}
        <div ref={chatBottomRef} />
      </div>

      {/* Bottom Query Input Bar */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSendMessage(inputQuery);
        }}
        className="border-t border-white/10 bg-white/[0.02] p-4 flex gap-2.5 items-center"
      >
        <input
          type="text"
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          placeholder="Ask a question about this document... (e.g. 'What are the payment terms?')"
          disabled={isSubmitting}
          className="flex-1 rounded-xl border border-white/15 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-white/40 focus:border-indigo-400 focus:bg-white/10 focus:outline-none transition-all disabled:opacity-50"
        />

        <button
          type="submit"
          disabled={!inputQuery.trim() || isSubmitting}
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-500 px-5 py-2.5 text-sm font-semibold text-white shadow-lg hover:from-indigo-400 hover:to-violet-400 active:scale-95 disabled:cursor-not-allowed disabled:opacity-40 transition-all shrink-0"
        >
          {isSubmitting ? (
            <>
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              <span>Thinking…</span>
            </>
          ) : (
            <>
              <span>Send</span>
              <span>→</span>
            </>
          )}
        </button>
      </form>
    </Card>
  );
}
