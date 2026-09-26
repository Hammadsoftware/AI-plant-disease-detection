import { LoaderCircle } from "lucide-react";
import { AssistantMessage } from "./AssistantMessage";

export function LoadingState({ message }: { message: string }) {
  return <AssistantMessage><div className="overflow-hidden rounded-[1.5rem] border border-emerald-950/9 bg-white p-6 shadow-[0_16px_50px_rgba(8,63,47,.06)]"><div className="flex items-center gap-3"><span className="relative grid size-11 place-items-center rounded-full bg-emerald-50 text-emerald-700"><span className="absolute inset-0 animate-ping rounded-full border border-emerald-300 opacity-25"/><LoaderCircle size={20} className="animate-spin"/></span><div><p className="font-semibold text-emerald-950">{message}</p><p className="mt-1 text-xs text-emerald-950/45">The status changes only when the diagnosis service reports a new phase.</p></div></div></div></AssistantMessage>;
}
