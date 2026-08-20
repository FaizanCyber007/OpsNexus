import Link from "next/link";
import type { ReactNode } from "react";

interface NavItem {
  label: string;
  href?: string;
  active?: boolean;
  icon: ReactNode;
}

const NAV_ITEMS: NavItem[] = [
  {
    label: "Dashboard",
    href: "/dashboard",
    active: true,
    icon: (
      <path
        d="M3 3h7v7H3V3Zm0 11h7v7H3v-7Zm11-11h7v7h-7V3Zm0 11h7v7h-7v-7Z"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    ),
  },
  {
    label: "Documents",
    icon: (
      <path
        d="M6 2.5h7l5 5V21a.5.5 0 0 1-.5.5h-11A.5.5 0 0 1 6 21V3a.5.5 0 0 1 .5-.5Zm7 0V7h5"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    ),
  },
  {
    label: "Agents",
    icon: (
      <>
        <circle cx="12" cy="12" r="3" strokeWidth="1.5" />
        <path
          d="M12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M2 12h3M19 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"
          strokeWidth="1.5"
          strokeLinecap="round"
        />
      </>
    ),
  },
  {
    label: "Settings",
    icon: (
      <>
        <circle cx="12" cy="12" r="3" strokeWidth="1.5" />
        <path
          d="M19.4 13a7.9 7.9 0 0 0 0-2l2-1.5-2-3.4-2.3 1a8 8 0 0 0-1.7-1L15 3h-4l-.4 2.6a8 8 0 0 0-1.7 1l-2.3-1-2 3.4L6.6 11a7.9 7.9 0 0 0 0 2l-2 1.5 2 3.4 2.3-1a8 8 0 0 0 1.7 1L11 21h4l.4-2.6a8 8 0 0 0 1.7-1l2.3 1 2-3.4-2-1.5Z"
          strokeWidth="1.5"
          strokeLinejoin="round"
        />
      </>
    ),
  },
] as const;

export function Sidebar() {
  return (
    <aside className="flex h-full w-60 flex-col border-r border-white/10 bg-white/5 backdrop-blur-xl">
      <div className="flex items-center gap-2 px-5 py-5">
        <svg viewBox="0 0 24 24" className="h-7 w-7 shrink-0" fill="none">
          <circle cx="6" cy="6" r="2.5" className="fill-indigo-400" />
          <circle cx="18" cy="6" r="2.5" className="fill-violet-400" />
          <circle cx="12" cy="18" r="2.5" className="fill-indigo-400" />
          <path
            d="M6 6 12 18M18 6 12 18M6 6h12"
            stroke="currentColor"
            strokeWidth="1.25"
            className="text-white/30"
          />
        </svg>
        <div>
          <p className="text-sm font-semibold leading-none text-white">OpsNexus</p>
          <p className="mt-1 text-[11px] leading-none text-white/40">Document Intake</p>
        </div>
      </div>

      <nav className="flex flex-col gap-1 px-3">
        {NAV_ITEMS.map((item) =>
          item.active && item.href ? (
            <Link
              key={item.label}
              href={item.href}
              className="flex items-center gap-3 rounded-lg bg-gradient-to-r from-indigo-500/20 to-violet-500/20 px-3 py-2 text-sm font-medium text-white ring-1 ring-inset ring-white/10"
            >
              <svg viewBox="0 0 24 24" className="h-4 w-4 text-indigo-300" fill="none" stroke="currentColor">
                {item.icon}
              </svg>
              {item.label}
            </Link>
          ) : (
            <div
              key={item.label}
              className="flex cursor-not-allowed items-center gap-3 rounded-lg px-3 py-2 text-sm text-white/35"
            >
              <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor">
                {item.icon}
              </svg>
              <span className="flex-1">{item.label}</span>
              <span className="rounded-full border border-white/10 px-1.5 py-0.5 text-[10px] text-white/30">
                Soon
              </span>
            </div>
          ),
        )}
      </nav>

      <div className="mt-auto border-t border-white/10 px-5 py-4">
        <p className="text-[11px] text-white/30">OpsNexus &middot; Phase 3 Scaffold</p>
      </div>
    </aside>
  );
}
