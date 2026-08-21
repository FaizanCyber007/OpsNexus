"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bot,
  User,
  Zap,
  Sparkles,
  Send,
  Trash2,
  Trophy,
  ChevronDown,
  ChevronUp,
  Database,
  ShieldAlert,
  CreditCard,
  ShieldCheck,
  ListCheck,
  Swords,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { ChatBubbleSkeleton } from "@/components/ui/Skeleton";
import { useToast } from "@/contexts/ToastContext";
import { apiClient } from "@/lib/apiClient";
import type { ChatMessage, Document, DocumentChunk } from "@/lib/types";
import { cn } from "@/lib/utils";

interface DocumentChatPanelProps {
  document: Document | null;
  documentId: string;
}

const PROMPT_SUGGESTIONS = [
  {
    icon: ShieldAlert,
    label: "Key Risks & Liabilities",
    prompt: "What are the primary risk factors, liabilities, or red flags identified in this document?",
  },
  {
    icon: CreditCard,
    label: "Payment & Commercial Terms",
    prompt: "What are the payment terms, billing cycles, pricing, or financial penalties specified?",
  },
  {
    icon: ShieldCheck,
    label: "Security & Compliance Clauses",
    prompt: "Are there any specific security, data privacy (GDPR/SOC2), or compliance requirements mentioned?",
  },
  {
    icon: ListCheck,
    label: "Action Items & Deliverables",
    prompt: "List all concrete action items, deliverables, and deadlines required by this document.",
  },
];

function ContextSnippetsDisclosure({ chunks }: { chunks: DocumentChunk[] }) {
  const [isOpen, setIsOpen] = useState(false);

  if (!chunks || chunks.length === 0) return null;

  return (
    <div className="mt-3 border-t border-white/[0.08] pt-2">
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="inline-flex items-center gap-1.5 text-[11px] font-medium text-indigo-400 hover:text-indigo-300 transition-colors"
      >
        <Database className="h-3 w-3" />
        <span>
          {isOpen
            ? "Hide Vector Context"
            : `View ${chunks.length} ChromaDB Context Chunk(s)`}
        </span>
        {isOpen ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
      </button>

      {isOpen && (
        <div className="mt-2.5 space-y-2 rounded-xl bg-black/50 p-3 border border-white/[0.06] text-xs">
          {chunks.map((chunk, idx) => (
            <div
              key={idx}
              className="space-y-1 border-b border-white/[0.04] pb-2.5 last:border-b-0 last:pb-0"
            >
              <div className="flex items-center justify-between text-[10px] text-white/40">
                <span className="font-mono text-indigo-300">Chunk #{idx + 1}</span>
                {chunk.distance != null && (
                  <span className="font-mono">Distance: {chunk.distance.toFixed(3)}</span>
                )}
              </div>
              <p className="whitespace-pre-wrap font-mono text-[11px] leading-relaxed text-white/70">
                {chunk.text}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function DocumentChatPanel({ documentId }: DocumentChatPanelProps) {
  const [isArenaMode, setIsArenaMode] = useState(true);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { showError, showSuccess } = useToast();
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
              results: response.results
                ? {
                    groq: response.results.groq,
                    gemini: response.results.gemini,
                  }
                : undefined,
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
      showError("Chat query failed or timed out. Please check backend connection.");
      console.error("Document chat error:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
    showSuccess("Chat session reset.");
  };

  return (
    <Card className="flex h-full min-h-[30rem] flex-col overflow-hidden p-0">
      {/* Top Header Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.08] bg-white/[0.02] px-5 py-3">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/20 text-indigo-300">
            <Swords className="h-4 w-4" />
          </div>
          <div>
            <h2 className="text-xs font-semibold text-white/95">RAG Intelligence & Model Arena</h2>
            <p className="text-[10px] text-white/40 font-mono">
              ChromaDB Vector Retrieval + Real-time LLM Benchmarking
            </p>
          </div>
        </div>

        {/* Right Toggle Bar */}
        <div className="flex items-center gap-3">
          {messages.length > 0 && (
            <button
              type="button"
              onClick={clearChat}
              disabled={isSubmitting}
              className="flex items-center gap-1 text-xs text-white/40 hover:text-white transition-colors disabled:opacity-40"
              title="Clear conversation"
            >
              <Trash2 className="h-3.5 w-3.5" />
              <span>Clear</span>
            </button>
          )}

          {/* Arena Switch */}
          <div className="flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.03] px-3 py-1">
            <span className="text-[11px] font-semibold text-white/80 flex items-center gap-1">
              <Zap className="h-3 w-3 text-amber-400" />
              <span>Model Arena</span>
            </span>
            <button
              type="button"
              role="switch"
              aria-checked={isArenaMode}
              onClick={() => setIsArenaMode((prev) => !prev)}
              className={cn(
                "relative inline-flex h-4 w-8 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none",
                isArenaMode ? "bg-indigo-600" : "bg-white/20"
              )}
            >
              <span
                aria-hidden="true"
                className={cn(
                  "pointer-events-none inline-block h-3 w-3 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out",
                  isArenaMode ? "translate-x-4" : "translate-x-0"
                )}
              />
            </button>
          </div>
        </div>
      </div>

      {/* Model Mode Banner */}
      <div className="border-b border-white/[0.04] bg-white/[0.01] px-5 py-1.5 text-[11px] flex items-center justify-between text-white/50">
        <div className="flex items-center gap-2">
          {isArenaMode ? (
            <>
              <span className="inline-flex items-center gap-1 rounded bg-amber-500/10 px-1.5 py-0.2 text-[10px] font-semibold text-amber-300 border border-amber-500/20">
                ⚡ Dual Benchmark
              </span>
              <span>Groq (Llama-3 70B) vs Gemini Flash</span>
            </>
          ) : (
            <>
              <span className="inline-flex items-center gap-1 rounded bg-indigo-500/10 px-1.5 py-0.2 text-[10px] font-semibold text-indigo-300 border border-indigo-500/20">
                Single Model
              </span>
              <span>Gemini Flash Standard Inference</span>
            </>
          )}
        </div>
      </div>

      {/* Messages Stream */}
      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        {messages.length === 0 ? (
          /* Empty Chat State with Prompts */
          <div className="flex flex-col items-center justify-center py-6 px-4 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-white/10 shadow-lg text-indigo-400 mb-3">
              <Sparkles className="h-6 w-6" />
            </div>
            <h3 className="text-sm font-semibold text-white/90 mb-1">
              Ask anything regarding this document
            </h3>
            <p className="text-xs text-white/40 max-w-sm mb-5 leading-relaxed">
              Synthesizes vector chunks from ChromaDB with real-time reasoning. Select a prompt or type below:
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full max-w-xl">
              {PROMPT_SUGGESTIONS.map((item, idx) => {
                const ItemIcon = item.icon;
                return (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSendMessage(item.prompt)}
                    disabled={isSubmitting}
                    className="flex items-start gap-3 rounded-xl border border-white/[0.08] bg-white/[0.02] p-3 text-left transition-all hover:bg-white/[0.06] hover:border-white/[0.14] active:scale-[0.98] disabled:opacity-50"
                  >
                    <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-400 shrink-0 mt-0.5">
                      <ItemIcon className="h-4 w-4" />
                    </div>
                    <div className="min-w-0">
                      <div className="text-xs font-semibold text-white/90">{item.label}</div>
                      <div className="text-[11px] text-white/40 line-clamp-1 mt-0.5 font-mono">
                        {item.prompt}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        ) : (
          <AnimatePresence initial={false}>
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2 }}
                className="space-y-3"
              >
                {/* User Message */}
                {msg.sender === "user" && (
                  <div className="flex justify-end">
                    <div className="max-w-[85%] rounded-2xl bg-gradient-to-r from-indigo-600 via-indigo-500 to-violet-600 px-4 py-2.5 text-xs text-white shadow-lg border border-white/10">
                      <div className="flex items-center justify-between gap-3 mb-1 text-[10px] text-white/70">
                        <span className="font-semibold flex items-center gap-1">
                          <User className="h-3 w-3" />
                          <span>You</span>
                        </span>
                        <span className="font-mono">{msg.timestamp}</span>
                      </div>
                      <p className="whitespace-pre-wrap leading-relaxed">{msg.question}</p>
                    </div>
                  </div>
                )}

                {/* Assistant Response */}
                {msg.sender === "assistant" && (
                  <div className="space-y-3">
                    {msg.compare ? (
                      /* Arena Split-View */
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {/* Groq Column */}
                        <div className="flex flex-col rounded-xl border border-amber-500/20 bg-amber-950/10 p-3.5 shadow-md">
                          <div className="flex items-center justify-between border-b border-amber-500/15 pb-2 mb-2.5">
                            <div className="flex items-center gap-1.5">
                              <span className="flex h-5 w-5 items-center justify-center rounded bg-amber-500/20 text-amber-300">
                                <Zap className="h-3 w-3" />
                              </span>
                              <span className="text-xs font-semibold text-amber-200">
                                Groq (Llama-3 70B)
                              </span>
                            </div>

                            <div className="flex items-center gap-1.5">
                              {msg.faster_model === "groq" && msg.time_diff_ms != null && (
                                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/20 border border-emerald-500/40 px-2 py-0.2 text-[10px] font-semibold text-emerald-300">
                                  <Trophy className="h-2.5 w-2.5" />
                                  <span>Faster by {msg.time_diff_ms}ms</span>
                                </span>
                              )}
                              {msg.results?.groq?.execution_time_ms !== undefined && (
                                <span className="rounded bg-white/10 px-1.5 py-0.2 font-mono text-[10px] text-white/70">
                                  {msg.results.groq.execution_time_ms}ms
                                </span>
                              )}
                            </div>
                          </div>

                          {msg.isPending ? (
                            <ChatBubbleSkeleton isArena={false} />
                          ) : (
                            <div className="text-xs leading-relaxed text-white/90 whitespace-pre-wrap flex-1">
                              {msg.results?.groq?.response || "No response received."}
                            </div>
                          )}
                        </div>

                        {/* Gemini Column */}
                        <div className="flex flex-col rounded-xl border border-indigo-500/20 bg-indigo-950/10 p-3.5 shadow-md">
                          <div className="flex items-center justify-between border-b border-indigo-500/15 pb-2 mb-2.5">
                            <div className="flex items-center gap-1.5">
                              <span className="flex h-5 w-5 items-center justify-center rounded bg-indigo-500/20 text-indigo-300">
                                <Sparkles className="h-3 w-3" />
                              </span>
                              <span className="text-xs font-semibold text-indigo-200">
                                Gemini Flash
                              </span>
                            </div>

                            <div className="flex items-center gap-1.5">
                              {msg.faster_model === "gemini" && msg.time_diff_ms != null && (
                                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/20 border border-emerald-500/40 px-2 py-0.2 text-[10px] font-semibold text-emerald-300">
                                  <Trophy className="h-2.5 w-2.5" />
                                  <span>Faster by {msg.time_diff_ms}ms</span>
                                </span>
                              )}
                              {msg.results?.gemini?.execution_time_ms !== undefined && (
                                <span className="rounded bg-white/10 px-1.5 py-0.2 font-mono text-[10px] text-white/70">
                                  {msg.results.gemini.execution_time_ms}ms
                                </span>
                              )}
                            </div>
                          </div>

                          {msg.isPending ? (
                            <ChatBubbleSkeleton isArena={false} />
                          ) : (
                            <div className="text-xs leading-relaxed text-white/90 whitespace-pre-wrap flex-1">
                              {msg.results?.gemini?.response || "No response received."}
                            </div>
                          )}
                        </div>
                      </div>
                    ) : (
                      /* Single Model Output */
                      <div className="rounded-xl border border-white/[0.08] bg-[#14141c]/80 p-3.5 shadow-md">
                        <div className="flex items-center justify-between border-b border-white/[0.06] pb-2 mb-2.5">
                          <div className="flex items-center gap-1.5">
                            <span className="flex h-5 w-5 items-center justify-center rounded bg-indigo-500/20 text-indigo-300">
                              <Bot className="h-3 w-3" />
                            </span>
                            <span className="text-xs font-semibold text-white/90">
                              {msg.result?.model_name || "OpsNexus AI"}
                            </span>
                          </div>
                          {msg.result?.execution_time_ms !== undefined && (
                            <span className="rounded bg-white/10 px-1.5 py-0.2 font-mono text-[10px] text-white/70">
                              {msg.result.execution_time_ms}ms
                            </span>
                          )}
                        </div>

                        {msg.isPending ? (
                          <ChatBubbleSkeleton isArena={false} />
                        ) : (
                          <div className="text-xs leading-relaxed text-white/90 whitespace-pre-wrap">
                            {msg.result?.response || "No response."}
                          </div>
                        )}
                      </div>
                    )}

                    {/* ChromaDB Context Snippets */}
                    {!msg.isPending && msg.retrieved_context && (
                      <ContextSnippetsDisclosure chunks={msg.retrieved_context} />
                    )}
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
        )}
        <div ref={chatBottomRef} />
      </div>

      {/* Input Bar */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSendMessage(inputQuery);
        }}
        className="border-t border-white/[0.08] bg-[#0d0d12]/90 p-3.5 flex gap-2 items-center"
      >
        <input
          type="text"
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          placeholder="Ask a question about this document... (Press Enter to query)"
          disabled={isSubmitting}
          className="flex-1 rounded-xl border border-white/[0.12] bg-white/[0.03] px-4 py-2 text-xs text-white placeholder-white/30 focus:border-indigo-400 focus:bg-white/[0.06] focus:outline-none transition-all shadow-inner disabled:opacity-50"
        />

        <button
          type="submit"
          disabled={!inputQuery.trim() || isSubmitting}
          className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-600 px-4 py-2 text-xs font-semibold text-white shadow-md shadow-indigo-500/20 hover:from-indigo-400 hover:to-violet-500 active:scale-95 disabled:cursor-not-allowed disabled:opacity-40 transition-all shrink-0"
        >
          {isSubmitting ? (
            <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
          ) : (
            <>
              <span>Query</span>
              <Send className="h-3 w-3" />
            </>
          )}
        </button>
      </form>
    </Card>
  );
}
