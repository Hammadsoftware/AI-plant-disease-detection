import { AlertTriangle, Plus, RotateCcw } from "lucide-react";
import { AssistantMessage } from "./AssistantMessage";

export function ErrorState({ message, onRetry, onNewScan }: { message: string; onRetry: () => void; onNewScan: () => void }) {
  return <AssistantMessage><div role="alert" className="rounded-[1.4rem] border border-red-200 bg-red-50/65 p-5"><div className="flex gap-3"><span className="grid size-10 shrink-0 place-items-center rounded-xl bg-red-100 text-red-700"><AlertTriangle size={19}/></span><div><h3 className="font-semibold text-red-950">Analysis not completed</h3><p className="mt-2 text-sm leading-6 text-red-900/65">{message}</p><div className="mt-4 flex flex-wrap gap-4"><button onClick={onRetry} className="inline-flex items-center gap-2 text-sm font-semibold text-red-800 hover:text-red-950"><RotateCcw size={15}/> Retry</button><button onClick={onNewScan} className="inline-flex items-center gap-2 text-sm font-semibold text-emerald-800 hover:text-emerald-950"><Plus size={15}/> New scan</button></div></div></div></div></AssistantMessage>;
}
