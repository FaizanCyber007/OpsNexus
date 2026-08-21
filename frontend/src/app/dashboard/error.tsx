"use client";

import { useEffect } from "react";

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
    console.error(error);
  }, [error]);

  return (
    <div className="flex flex-1 items-center justify-center p-10">
      <Card className="flex max-w-md flex-col items-center gap-3 text-center">
        <div className="flex h-10 w-10 items-center justify-center rounded-full border border-status-critical/30 bg-status-critical/10 text-status-critical">
          <svg viewBox="0 0 16 16" className="h-5 w-5" fill="none">
            <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5" />
            <path
              d="M5.5 5.5 10.5 10.5M10.5 5.5 5.5 10.5"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
        </div>
        <h2 className="text-base font-semibold text-white">Something went wrong</h2>
        <p className="text-sm text-white/50">
          The dashboard hit an unexpected error. You can try again, or reload the page.
        </p>
        <Button onClick={() => reset()}>Try again</Button>
      </Card>
    </div>
  );
}
