"use client";

import Link from "next/link";
import { ArrowUpRight, Menu, X } from "lucide-react";
import { useEffect, useState } from "react";
import { Logo } from "./Logo";

const links = [
  ["How It Works", "#how-it-works"],
  ["AI Diagnosis", "#diagnosis"],
  ["Evidence", "#evidence"],
  ["Treatment", "#treatment"],
] as const;

export function Navbar() {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const update = () => setScrolled(window.scrollY > 12);
    update();
    window.addEventListener("scroll", update, { passive: true });
    return () => window.removeEventListener("scroll", update);
  }, []);

  return (
    <header className={`fixed inset-x-0 top-0 z-50 transition-all ${scrolled ? "border-b border-emerald-950/8 bg-[#f7faf5]/90 shadow-[0_8px_30px_rgba(9,64,48,.05)] backdrop-blur-xl" : "bg-transparent"}`}>
      <nav className="page-shell flex h-20 items-center justify-between" aria-label="Main navigation">
        <Logo />
        <div className="hidden items-center gap-8 lg:flex">
          {links.map(([label, href]) => (
            <Link key={href} href={href} className="text-sm font-medium text-emerald-950/65 transition hover:text-emerald-700">
              {label}
            </Link>
          ))}
        </div>
        <Link href="/dashboard" className="button-primary hidden sm:inline-flex">
          Start Diagnosis <ArrowUpRight size={16} aria-hidden="true" />
        </Link>
        <button className="grid size-11 place-items-center rounded-xl border border-emerald-950/10 text-emerald-950 sm:hidden" onClick={() => setOpen((value) => !value)} aria-label={open ? "Close menu" : "Open menu"} aria-expanded={open}>
          {open ? <X size={20} /> : <Menu size={20} />}
        </button>
      </nav>
      {open && (
        <div className="border-t border-emerald-950/8 bg-[#f7faf5] px-5 pb-6 pt-4 sm:hidden">
          <div className="flex flex-col gap-1">
            {links.map(([label, href]) => (
              <Link key={href} href={href} onClick={() => setOpen(false)} className="rounded-xl px-4 py-3 text-sm font-medium text-emerald-950/75 hover:bg-emerald-50">{label}</Link>
            ))}
            <Link href="/dashboard" className="button-primary mt-3 justify-center">Start Diagnosis</Link>
          </div>
        </div>
      )}
    </header>
  );
}
