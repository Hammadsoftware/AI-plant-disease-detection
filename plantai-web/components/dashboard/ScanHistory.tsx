import { Clock3, Trash2 } from "lucide-react";
import Image from "next/image";
import type { HistoryItem } from "@/lib/types";
import { historyDate } from "@/lib/utils";

interface ScanHistoryProps { history: HistoryItem[]; onSelect: (item: HistoryItem) => void; onDelete: (id: string) => void; }

export function ScanHistory({ history, onSelect, onDelete }: ScanHistoryProps) {
  if (!history.length) return <div className="rounded-2xl border border-dashed border-emerald-950/12 px-4 py-6 text-center"><Clock3 className="mx-auto text-emerald-800/25" size={21}/><p className="mt-3 text-xs leading-5 text-emerald-950/38">Your completed scans will appear here.</p></div>;
  return <div className="space-y-2">{history.map((item) => <div key={item.id} className="group relative"><button onClick={() => onSelect(item)} className="flex w-full items-center gap-3 rounded-2xl p-2 text-left transition hover:bg-emerald-50"><Image src={item.imagePreview} alt="" width={44} height={44} unoptimized className="size-11 shrink-0 rounded-xl bg-emerald-100 object-cover"/><span className="min-w-0 pr-7"><span className="block truncate text-xs font-semibold text-emerald-950/75">{item.disease}</span><span className="mt-1 block text-[10px] text-emerald-950/38">{historyDate(item.timestamp)}</span></span></button><button onClick={() => onDelete(item.id)} aria-label={`Delete ${item.disease} scan`} className="absolute right-2 top-1/2 grid size-7 -translate-y-1/2 place-items-center rounded-lg text-emerald-950/25 opacity-0 transition hover:bg-red-50 hover:text-red-600 group-hover:opacity-100 group-focus-within:opacity-100"><Trash2 size={13}/></button></div>)}</div>;
}
