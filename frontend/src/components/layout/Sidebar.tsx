"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  LayoutDashboard,
  FileText,
  ShieldCheck,
  Settings,
  Zap,
  Building,
} from "lucide-react";

import { useTenant, DEMO_ORG_ID } from "@/contexts/TenantContext";
import { cn } from "@/lib/utils";

interface NavItem {
  label: string;
  href: string;
  icon: typeof LayoutDashboard;
  description: string;
}

const NAV_ITEMS: NavItem[] = [
  {
    label: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
    description: "Overview & Upload",
  },
  {
    label: "Documents",
    href: "/dashboard/documents",
    icon: FileText,
    description: "Browse & Search",
  },
  {
    label: "AI Swarm & Tools",
    href: "/dashboard/agents",
    icon: Zap,
    description: "AI Models & Policies",
  },
  {
    label: "Activity & Security",
    href: "/dashboard/audit",
    icon: ShieldCheck,
    description: "Audit Log & History",
  },
  {
    label: "Rules & Settings",
    href: "/dashboard/settings",
    icon: Settings,
    description: "Alerts & Guides",
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { organizationId } = useTenant();

  const workspaceName = organizationId
    ? organizationId === DEMO_ORG_ID
      ? "Main Workspace"
      : "Company Workspace"
    : "Main Workspace";

  return (
    <aside className="relative flex h-full w-64 flex-col border-r border-white/[0.08] bg-[#0c0c10]/95 backdrop-blur-2xl select-none z-20">
      {/* Brand Header */}
      <div className="flex items-center justify-between px-5 py-5 border-b border-white/[0.06]">
        <Link href="/dashboard" className="flex items-center gap-3 group">
          <div className="relative flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 via-indigo-600 to-violet-600 shadow-lg shadow-indigo-500/25 border border-white/20 group-hover:scale-105 transition-transform">
            <Zap className="h-4 w-4 text-white fill-white/80" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-sm font-bold tracking-tight text-white">OpsNexus</span>
              <span className="rounded bg-indigo-500/20 px-1.5 py-0.2 text-[9px] font-semibold text-indigo-300 border border-indigo-500/30">
                AI
              </span>
            </div>
            <p className="text-[11px] text-white/40">Document Intelligence</p>
          </div>
        </Link>
      </div>

      {/* Workspace Indicator */}
      <div className="px-3 pt-3 pb-1">
        <div className="flex items-center justify-between rounded-xl border border-white/[0.06] bg-white/[0.02] px-3 py-2 text-xs text-white/70">
          <div className="flex items-center gap-2 min-w-0">
            <span className="h-2 w-2 shrink-0 rounded-full bg-emerald-400" />
            <span className="font-medium text-white/90 truncate">{workspaceName}</span>
          </div>
          <Building className="h-3.5 w-3.5 text-white/40 shrink-0" />
        </div>
      </div>

      {/* Nav List */}
      <nav className="flex-1 space-y-1 px-3 py-3">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive =
            item.href === "/dashboard"
              ? pathname === "/dashboard"
              : pathname.startsWith(item.href);

          return (
            <Link
              key={item.label}
              href={item.href}
              className={cn(
                "relative flex items-center justify-between rounded-xl px-3 py-2.5 text-xs font-semibold transition-all group",
                isActive
                  ? "text-white"
                  : "text-white/60 hover:text-white hover:bg-white/[0.04]"
              )}
            >
              {isActive && (
                <motion.div
                  layoutId="sidebarActiveBackground"
                  className="absolute inset-0 rounded-xl bg-gradient-to-r from-indigo-500/25 via-violet-500/20 to-transparent border border-indigo-500/30 shadow-inner"
                  transition={{ type: "spring", stiffness: 350, damping: 30 }}
                />
              )}
              <div className="relative z-10 flex items-center gap-2.5">
                <Icon
                  className={cn(
                    "h-4 w-4 transition-colors",
                    isActive
                      ? "text-indigo-400"
                      : "text-white/40 group-hover:text-indigo-300"
                  )}
                />
                <div>
                  <span className="block">{item.label}</span>
                </div>
              </div>
            </Link>
          );
        })}
      </nav>

      {/* Footer Status Widget */}
      <div className="mt-auto border-t border-white/[0.06] p-4 space-y-1.5">
        <div className="flex items-center justify-between text-[11px]">
          <div className="flex items-center gap-2 text-white/60">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="font-medium">AI Ready</span>
          </div>
          <span className="text-white/30 text-[10px]">Secure & Private</span>
        </div>
      </div>
    </aside>
  );
}
