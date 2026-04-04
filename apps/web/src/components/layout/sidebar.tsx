"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, Target, UtensilsCrossed } from "lucide-react";

const navItems = [
  { href: "/", icon: Target, label: "Plan" },
  { href: "/aerobico", icon: Activity, label: "Aeróbico" },
  { href: "/nutricion", icon: UtensilsCrossed, label: "Nutrición" },
] as const;

export function Sidebar() {
  const pathname = usePathname();

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="bg-bg-card fixed left-0 top-0 z-40 hidden h-screen w-[72px] flex-col items-center py-6 shadow-[1px_0_0_0_rgba(255,255,255,0.04)] md:flex">
        <Link
          href="/"
          className="font-heading mb-8 flex h-10 w-10 items-center justify-center rounded-lg text-sm font-bold tracking-tight text-text-primary"
        >
          GP
        </Link>

        <nav className="flex flex-1 flex-col items-center gap-1">
          {navItems.map(({ href, icon: Icon, label }) => {
            const isActive =
              href === "/" ? pathname === "/" : pathname.startsWith(href);
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
                <span className="pointer-events-none absolute left-full ml-3 rounded-md bg-bg-hover px-2.5 py-1.5 text-xs font-medium text-text-primary opacity-0 shadow-lg transition-opacity duration-150 group-hover:opacity-100">
                  {label}
                </span>
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Mobile bottom nav */}
      <nav className="bg-bg-card fixed bottom-0 left-0 right-0 z-40 flex items-center justify-around border-t border-white/5 pb-[env(safe-area-inset-bottom)] md:hidden">
        {navItems.map(({ href, icon: Icon, label }) => {
          const isActive =
            href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`flex flex-col items-center gap-0.5 px-2 py-2 ${
                isActive ? "text-text-primary" : "text-text-secondary"
              }`}
            >
              <Icon size={18} strokeWidth={isActive ? 2 : 1.5} />
              <span className="text-[9px] font-medium">{label}</span>
            </Link>
          );
        })}
      </nav>
    </>
  );
}
