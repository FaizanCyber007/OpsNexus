"use client";

import { useState } from "react";
import { Check, Copy, CheckCheck } from "lucide-react";
import { cn } from "@/lib/utils";

interface ActionItemChecklistProps {
  items: string[];
  className?: string;
}

export function ActionItemChecklist({ items, className = "" }: ActionItemChecklistProps) {
  const [completed, setCompleted] = useState<Record<number, boolean>>({});
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);

  const toggleItem = (index: number) => {
    setCompleted((prev) => ({ ...prev, [index]: !prev[index] }));
  };

  const copyItemText = (index: number, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedIdx(index);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  return (
    <ul className={cn("flex flex-col gap-2", className)}>
      {items.map((item, index) => {
        const isDone = Boolean(completed[index]);
        const isCopied = copiedIdx === index;

        return (
          <li
            key={`${index}-${item}`}
            className={cn(
              "group flex items-start gap-3 rounded-xl border border-white/[0.06] bg-white/[0.02] p-3 text-xs transition-all hover:bg-white/[0.05] hover:border-white/[0.12]",
              isDone && "opacity-60 bg-transparent border-white/[0.03]"
            )}
          >
            <button
              type="button"
              onClick={() => toggleItem(index)}
              aria-label={isDone ? "Mark incomplete" : "Mark complete"}
              className={cn(
                "mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-md border transition-all",
                isDone
                  ? "border-emerald-500 bg-emerald-500 text-white"
                  : "border-white/30 hover:border-indigo-400 bg-black/20"
              )}
            >
              {isDone && <Check className="h-3 w-3 stroke-[2.5]" />}
            </button>

            <span
              onClick={() => toggleItem(index)}
              className={cn(
                "flex-1 cursor-pointer select-none leading-relaxed text-white/80 transition-colors group-hover:text-white",
                isDone && "line-through text-white/40"
              )}
            >
              {item}
            </span>

            <button
              type="button"
              onClick={() => copyItemText(index, item)}
              title="Copy action item"
              className="opacity-0 group-hover:opacity-100 text-white/40 hover:text-white transition-opacity p-0.5"
            >
              {isCopied ? (
                <CheckCheck className="h-3.5 w-3.5 text-emerald-400" />
              ) : (
                <Copy className="h-3.5 w-3.5" />
              )}
            </button>
          </li>
        );
      })}
    </ul>
  );
}
