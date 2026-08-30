import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";

import { ToastProvider } from "@/contexts/ToastContext";
import { TenantProvider } from "@/contexts/TenantContext";
import { ThreeBackground } from "@/components/ui/ThreeBackground";

import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "OpsNexus — Autonomous Enterprise Document Intelligence",
  description:
    "Autonomous back-office document intake, multi-agent reasoning, semantic ChromaDB retrieval, and MCP policy enforcement.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased dark`}
    >
      <body className="min-h-full flex flex-col bg-[#09090b] text-[#f4f4f5] relative selection:bg-indigo-500/30 selection:text-white" suppressHydrationWarning>
        <ThreeBackground />
        <div className="relative z-10 flex min-h-screen flex-col">
          <TenantProvider>
            <ToastProvider>{children}</ToastProvider>
          </TenantProvider>
        </div>
      </body>
    </html>
  );
}
