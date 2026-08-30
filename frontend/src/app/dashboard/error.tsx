"use client";

import { useEffect } from "react";
import Link from "next/link";
import { AlertTriangle, RefreshCw, ArrowLeft, Terminal } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Dashboard error boundary triggered:", error);
  }, [error]);

  return (
    <div className="flex flex-1 items-center justify-center p-6 sm:p-10">
      <Card className="flex max-w-lg flex-col items-center gap-4 text-center border-rose-500/20 bg-[#161114]/90 shadow-2xl">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-rose-500/30 bg-rose-500/10 text-rose-400 shadow-inner">
          <AlertTriangle className="h-6 w-6 stroke-[1.75]" />
        </div>

        <div>
          <h2 className="text-base font-bold text-white">Dashboard Runtime Anomaly</h2>
          <p className="mt-1.5 text-xs text-white/60 leading-relaxed max-w-sm">
            OpsNexus encountered an unhandled exception while loading dashboard assets or executing agent synchronization.
          </p>
        </div>

        {error.message && (
          <div className="w-full rounded-xl bg-black/40 p-3 border border-white/5 text-left">
            <div className="flex items-center gap-1.5 text-[10px] font-mono text-white/40 mb-1">
              <Terminal className="h-3 w-3" />
              <span>DIAGNOSTIC LOG</span>
            </div>
            <p className="font-mono text-xs text-rose-300 break-words">
              {error.message}
            </p>
            {error.digest && (
              <p className="mt-1 font-mono text-[10px] text-white/30">
                Digest: {error.digest}
              </p>
            )}
          </div>
        )}

        <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
          <Link href="/dashboard">
            <Button variant="secondary" size="sm" leftIcon={<ArrowLeft className="h-3.5 w-3.5" />}>
              Reset View
            </Button>
          </Link>
          <Button
            variant="primary"
            size="sm"
            onClick={() => reset()}
            leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
          >
            Try Again
          </Button>
        </div>
      </Card>
    </div>
  );
}
