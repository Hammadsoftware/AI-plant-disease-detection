import Link from "next/link";
import { History, Info, Plus, X } from "lucide-react";
import type { HistoryItem, ServiceStatus } from "@/lib/types";
import { Logo } from "@/components/landing/Logo";
import { ScanHistory } from "./ScanHistory";
import { ServiceStatus as StatusIndicator } from "./ServiceStatus";

interface SidebarProps { open: boolean; onClose: () => void; onNewScan: () => void; history: HistoryItem[]; onSelectHistory: (item: HistoryItem) => void; onDeleteHistory: (id: string) => void; serviceStatus: ServiceStatus; }

export function Sidebar(props: SidebarProps) {
  const content = <><div className="flex h-20 items-center justify-between px-5"><Logo/><button className="grid size-9 place-items-center rounded-xl text-emerald-950/50 lg:hidden" onClick={props.onClose} aria-label="Close sidebar"><X size={19}/></button></div><div className="px-3"><button onClick={props.onNewScan} className="flex w-full items-center gap-3 rounded-xl bg-emerald-950 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-emerald-950/10"><Plus size={17} className="text-lime-300"/>New Scan</button><nav className="mt-3 space-y-1" aria-label="Dashboard navigation"><button className="flex w-full items-center gap-3 rounded-xl bg-emerald-50 px-4 py-3 text-left text-sm font-medium text-emerald-800"><History size={17}/>History</button><Link href="/#how-it-works" className="flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-emerald-950/55 hover:bg-emerald-50"><Info size={17}/>About</Link></nav></div><div className="mt-7 flex min-h-0 flex-1 flex-col px-3"><p className="px-2 text-[10px] font-bold uppercase tracking-[.15em] text-emerald-950/35">Previous scans</p><div className="mt-3 min-h-0 flex-1 overflow-y-auto"><ScanHistory history={props.history} onSelect={props.onSelectHistory} onDelete={props.onDeleteHistory}/></div></div><div className="border-t border-emerald-950/8 p-5"><StatusIndicator status={props.serviceStatus}/></div></>;
  return <><aside className="hidden h-dvh w-[280px] shrink-0 flex-col border-r border-emerald-950/8 bg-[#f7faf5] lg:flex">{content}</aside>{props.open && <div className="fixed inset-0 z-50 bg-emerald-950/40 backdrop-blur-sm lg:hidden" onMouseDown={(event) => { if (event.target === event.currentTarget) props.onClose(); }}><aside className="flex h-full w-[min(84vw,300px)] flex-col bg-[#f7faf5] shadow-2xl">{content}</aside></div>}</>;
}
