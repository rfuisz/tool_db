"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LocalRenderSyncButton } from "@/components/local-render-sync-button";

const NAV_ITEMS = [
  { href: "/", label: "Home" },
  { href: "/items", label: "Toolkit" },
  { href: "/gaps", label: "Gaps" },
  { href: "/workflows", label: "Workflows" },
  { href: "/api", label: "API" },
];

export function Nav({
  showFirstPass = false,
  showLocalAdmin = false,
}: {
  showFirstPass?: boolean;
  showLocalAdmin?: boolean;
}) {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);
  const navItems = showFirstPass
    ? [...NAV_ITEMS.slice(0, 2), { href: "/first-pass", label: "First Pass" }, ...NAV_ITEMS.slice(2)]
    : NAV_ITEMS;

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-surface/90 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-6">
        <Link
          href="/"
          className="flex items-center gap-3 text-ink"
        >
          <Image
            src="/logo.svg"
            alt=""
            aria-hidden="true"
            width={36}
            height={36}
            className="h-9 w-9 shrink-0"
          />
          <span className="font-display text-xl font-bold tracking-tight">
            BioControl<span className="text-accent">Toolkit</span>
          </span>
        </Link>

        <button
          type="button"
          aria-label={menuOpen ? "Close navigation menu" : "Open navigation menu"}
          aria-expanded={menuOpen}
          aria-controls="site-nav-mobile"
          onClick={() => setMenuOpen((open) => !open)}
          className="flex h-10 w-10 items-center justify-center text-ink transition-colors hover:text-accent md:hidden"
        >
          <span className="sr-only">Menu</span>
          <span className="relative block h-4 w-4">
            <span
              className={`absolute top-0 left-0 block h-px w-full bg-current transition-all ${
                menuOpen ? "top-1/2 -translate-y-1/2 rotate-45" : ""
              }`}
            />
            <span
              className={`absolute top-1/2 left-0 block h-px w-full -translate-y-1/2 bg-current transition-opacity ${
                menuOpen ? "opacity-0" : ""
              }`}
            />
            <span
              className={`absolute bottom-0 left-0 block h-px w-full bg-current transition-all ${
                menuOpen ? "top-1/2 -translate-y-1/2 -rotate-45" : ""
              }`}
            />
          </span>
        </button>

        <div className="hidden items-center gap-4 md:flex">
          {navItems.map((item) => {
            const active =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`small-caps transition-colors ${
                  active
                    ? "text-ink"
                    : "text-ink-muted hover:text-ink-secondary"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
          {showLocalAdmin && <LocalRenderSyncButton variant="nav" />}
        </div>
      </div>
      {menuOpen && (
        <div
          id="site-nav-mobile"
          className="border-t border-edge bg-surface md:hidden"
        >
          <div className="mx-auto flex max-w-5xl flex-col px-6 py-4">
            {navItems.map((item) => {
              const active =
                item.href === "/"
                  ? pathname === "/"
                  : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMenuOpen(false)}
                  className={`small-caps border-b border-edge py-3 transition-colors last:border-b-0 ${
                    active
                      ? "text-ink"
                      : "text-ink-muted hover:text-ink-secondary"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
            {showLocalAdmin && (
              <div className="pt-4">
                <LocalRenderSyncButton variant="nav" />
              </div>
            )}
          </div>
        </div>
      )}
      <div className="rule-accent mx-auto h-px max-w-5xl" />
    </nav>
  );
}
