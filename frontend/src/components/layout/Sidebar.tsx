"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  LayoutDashboard,
  FileText,
  Bot,
  Settings,
  Zap,
  Layers,
} from "lucide-react";

interface NavItem {
  label: string;
  href?: string;
  icon: typeof LayoutDashboard;
  shortcut?: string;
  badge?: string;
}

const NAV_ITEMS: NavItem[] = [
  {
    label: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
    shortcut: "⌘D",
  },
  {
    label: "Documents",
    icon: FileText,
    badge: "Soon",
  },
  {
    label: "Agents & MCP",
    icon: Bot,
    badge: "Soon",
  },
  {
    label: "Settings",
    icon: Settings,
    badge: "Soon",
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="relative flex h-full w-64 flex-col border-r border-white/[0.08] bg-[#0c0c10]/90 backdrop-blur-2xl select-none z-20">
      {/* Brand Header */}
      <div className="flex items-center justify-between px-5 py-5 border-b border-white/[0.06]">
        <Link href="/dashboard" className="flex items-center gap-3 group">
          <div className="relative flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 via-indigo-600 to-violet-600 shadow-lg shadow-indigo-500/25 border border-white/20 group-hover:scale-105 transition-transform">
            <Zap className="h-4 w-4 text-white fill-white/80" />
            <div className="absolute inset-0 rounded-xl bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-sm font-bold tracking-tight text-white">OpsNexus</span>
              <span className="rounded bg-indigo-500/20 px-1 py-0.2 text-[9px] font-semibold text-indigo-300 border border-indigo-500/30">
                PRO
              </span>
            </div>
            <p className="text-[11px] text-white/40 font-mono">Autonomous Back-Office</p>
          </div>
        </Link>
      </div>

      {/* Workspace Indicator */}
      <div className="px-3 pt-3 pb-1">
        <div className="flex items-center justify-between rounded-xl border border-white/[0.06] bg-white/[0.02] px-3 py-2 text-xs text-white/70">
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="font-medium text-white/90">Production Org</span>
          </div>
          <Layers className="h-3.5 w-3.5 text-white/40" />
        </div>
      </div>

      {/* Nav List */}
      <nav className="flex-1 space-y-1 px-3 py-3">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive =
            Boolean(item.href) &&
            (pathname === item.href ||
              (item.href !== "/" && pathname.startsWith(item.href ?? "")));

          if (isActive && item.href) {
            return (
              <Link
                key={item.label}
                href={item.href}
                className="relative flex items-center justify-between rounded-xl px-3 py-2 text-xs font-semibold text-white transition-colors"
              >
                <motion.div
                  layoutId="sidebarActiveBackground"
                  className="absolute inset-0 rounded-xl bg-gradient-to-r from-indigo-500/20 via-violet-500/15 to-transparent border border-indigo-500/30 shadow-inner"
                  transition={{ type: "spring", stiffness: 350, damping: 30 }}
                />
                <div className="relative z-10 flex items-center gap-2.5">
                  <Icon className="h-4 w-4 text-indigo-300" />
                  <span>{item.label}</span>
                </div>
                {item.shortcut && (
                  <span className="relative z-10 font-mono text-[10px] text-white/40">
                    {item.shortcut}
                  </span>
                )}
              </Link>
            );
          }

          return (
            <div
              key={item.label}
              className="flex items-center justify-between rounded-xl px-3 py-2 text-xs text-white/40 cursor-not-allowed transition-colors hover:text-white/60"
            >
              <div className="flex items-center gap-2.5">
                <Icon className="h-4 w-4 stroke-[1.75]" />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className="rounded-md border border-white/[0.08] bg-white/[0.02] px-1.5 py-0.5 text-[9px] font-mono text-white/30">
                  {item.badge}
                </span>
              )}
            </div>
          );
        })}
      </nav>

      {/* Footer Status Widget */}
      <div className="mt-auto border-t border-white/[0.06] p-4 space-y-2">
        <div className="flex items-center justify-between text-[11px]">
          <div className="flex items-center gap-2 text-white/50">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            <span>Agent Cluster Online</span>
          </div>
          <span className="font-mono text-white/30 text-[10px]">v1.4.2</span>
        </div>
      </div>
    </aside>
  );
}
