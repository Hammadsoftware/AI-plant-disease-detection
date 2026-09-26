import Link from "next/link";
import { Logo } from "./Logo";

export function Footer() {
  return <footer className="bg-white py-10"><div className="page-shell flex flex-col items-center justify-between gap-5 border-t border-emerald-950/8 pt-8 sm:flex-row"><Logo/><p className="text-sm text-emerald-950/45">AI-assisted insights should complement local professional advice.</p><Link href="/dashboard" className="text-sm font-semibold text-emerald-700 hover:text-emerald-900">Open PlantAI</Link></div></footer>;
}
