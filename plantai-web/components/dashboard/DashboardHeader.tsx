import { Menu, Plus } from "lucide-react";
import type { ServiceStatus } from "@/lib/types";
import { Logo } from "@/components/landing/Logo";
import { ServiceStatus as StatusIndicator } from "./ServiceStatus";

export function DashboardHeader({ onMenu, onNewScan, status }: { onMenu: () => void; onNewScan: () => void; status: ServiceStatus }) {
  return (
    <header className="flex h-20 shrink-0 items-center justify-between border-b border-emerald-950/8 bg-white/85 px-4 backdrop-blur-xl sm:px-6">
      <div className="flex items-center gap-3 lg:hidden">
        <button onClick={onMenu} className="grid size-10 place-items-center rounded-xl border border-emerald-950/10 text-emerald-950" aria-label="Open sidebar"><Menu size={19}/></button>
        <Logo/>
      </div>
      <div className="hidden lg:block"><p className="text-sm font-semibold text-emerald-950">Plant diagnosis</p><p className="mt-1 text-xs text-emerald-950/40">A focused conversation with your leaf image</p></div>
      <div className="flex items-center gap-4">
        <div className="hidden sm:block lg:hidden"><StatusIndicator status={status} compact/></div>
        <button onClick={onNewScan} className="inline-flex items-center gap-2 rounded-full bg-emerald-950 px-3 py-2.5 text-xs font-semibold text-white transition hover:bg-emerald-800 sm:px-4 sm:text-sm"><Plus size={16} className="text-lime-300"/><span>New Scan</span></button>
      </div>
    </header>
  );
}
