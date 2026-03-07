"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Apple,
  Heart,
  LayoutDashboard,
  Moon,
  Settings,
  TrendingUp,
} from "lucide-react";

const navItems = [
  { href: "/", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/performance", icon: TrendingUp, label: "Performance" },
  { href: "/sleep", icon: Moon, label: "Sleep" },
  { href: "/nutrition", icon: Apple, label: "Nutrition" },
  { href: "/body", icon: Heart, label: "Body" },
] as const;

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="bg-bg-card fixed left-0 top-0 z-40 flex h-screen w-[72px] flex-col items-center py-6 shadow-[1px_0_0_0_rgba(255,255,255,0.04)]">
      {/* Brand mark */}
      <Link
        href="/"
        className="font-heading mb-8 flex h-10 w-10 items-center justify-center rounded-lg text-sm font-bold tracking-tight text-text-primary"
      >
        GP
      </Link>

      {/* Navigation */}
      <nav className="flex flex-1 flex-col items-center gap-1">
        {navItems.map(({ href, icon: Icon, label }) => {
          const isActive = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`group relative flex h-11 w-11 items-center justify-center rounded-lg transition-all duration-200 ${
                isActive
                  ? "bg-bg-hover text-text-primary"
                  : "text-text-secondary hover:bg-bg-hover/50 hover:text-text-primary"
              }`}
            >
              <Icon size={20} strokeWidth={isActive ? 2 : 1.5} />
              {/* Tooltip */}
              <span className="pointer-events-none absolute left-full ml-3 rounded-md bg-bg-hover px-2.5 py-1.5 text-xs font-medium text-text-primary opacity-0 shadow-lg transition-opacity duration-150 group-hover:opacity-100">
                {label}
              </span>
            </Link>
          );
        })}
      </nav>

      {/* Settings at bottom */}
      <Link
        href="/settings"
        className="text-text-secondary hover:bg-bg-hover/50 flex h-11 w-11 items-center justify-center rounded-lg transition-all duration-200 hover:text-text-primary"
      >
        <Settings size={20} strokeWidth={1.5} />
      </Link>
    </aside>
  );
}
