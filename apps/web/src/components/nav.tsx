"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Home" },
  { href: "/items", label: "Collection" },
  { href: "/workflows", label: "Workflows" },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-surface/90 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-6">
        <Link href="/" className="font-display text-xl font-bold tracking-tight text-ink">
          BioControl<span className="text-accent">Toolkit</span>
        </Link>

        <div className="flex items-center gap-6">
          {NAV_ITEMS.map((item) => {
            const active =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`small-caps transition-colors ${
                  active ? "text-ink" : "text-ink-muted hover:text-ink-secondary"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </div>
      </div>
      <div className="rule-accent mx-auto h-px max-w-5xl" />
    </nav>
  );
}
