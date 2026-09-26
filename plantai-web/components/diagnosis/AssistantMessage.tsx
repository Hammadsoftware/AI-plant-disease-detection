import { Sparkles } from "lucide-react";

export function AssistantMessage({ children }: { children: React.ReactNode }) {
  return <div className="max-w-3xl"><div className="mb-4 flex items-center gap-2.5"><span className="grid size-8 place-items-center rounded-xl bg-emerald-950 text-lime-300"><Sparkles size={15}/></span><span className="text-sm font-semibold text-emerald-950">PlantAI</span></div><div className="pl-0 sm:pl-[2.625rem]">{children}</div></div>;
}
