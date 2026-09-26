import { BookOpenCheck, Check, FileSearch, Link2, Sparkles } from "lucide-react";

const features = [
  ["Disease identification", "The model prediction remains clearly separated from supporting research."],
  ["Research evidence", "When enabled, returned evidence is organized into a readable summary."],
  ["Treatment guidance", "Guidance appears only when the backend provides it."],
  ["Supporting sources", "Source links stay attached to the claims they help explain."],
] as const;

export function EvidenceSection() {
  return (
    <section id="evidence" className="section-padding bg-[#f3f7f1]">
      <div className="page-shell grid items-center gap-16 lg:grid-cols-2">
        <div className="relative mx-auto w-full max-w-xl rounded-[2rem] border border-emerald-950/10 bg-white p-5 shadow-[0_30px_80px_rgba(8,63,47,.11)] sm:p-7">
          <div className="flex items-center justify-between border-b border-emerald-950/8 pb-5"><div className="flex items-center gap-3"><span className="grid size-10 place-items-center rounded-xl bg-emerald-950 text-lime-300"><Sparkles size={18} /></span><div><p className="text-sm font-semibold text-emerald-950">PlantAI evidence</p><p className="text-xs text-emerald-950/45">Structured by the diagnostic service</p></div></div><span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">Connected</span></div>
          <div className="mt-6 rounded-2xl bg-emerald-950 p-6 text-white"><div className="flex items-center gap-2 text-sm text-emerald-100/60"><FileSearch size={17} className="text-lime-300" /> Evidence synthesis</div><div className="mt-6 space-y-3"><span className="block h-2 w-[86%] rounded-full bg-white/15"/><span className="block h-2 w-full rounded-full bg-white/10"/><span className="block h-2 w-[64%] rounded-full bg-white/10"/></div></div>
          <div className="mt-4 grid gap-4 sm:grid-cols-2"><div className="rounded-2xl border border-emerald-950/8 p-5"><BookOpenCheck size={20} className="text-emerald-700"/><p className="mt-5 text-sm font-semibold text-emerald-950">Research context</p><p className="mt-2 text-xs leading-5 text-emerald-950/48">Readable evidence, not a wall of data.</p></div><div className="rounded-2xl border border-emerald-950/8 p-5"><Link2 size={20} className="text-emerald-700"/><p className="mt-5 text-sm font-semibold text-emerald-950">Traceable sources</p><p className="mt-2 text-xs leading-5 text-emerald-950/48">Open the supporting links returned by the API.</p></div></div>
        </div>
        <div>
          <p className="section-kicker">Evidence, when available</p><h2 className="section-title mt-4">Diagnosis backed by evidence.</h2><p className="mt-6 max-w-xl text-lg leading-8 text-emerald-950/60">PlantAI can combine the vision model’s prediction with live research and supporting evidence when those services are enabled by the backend.</p>
          <div className="mt-9 space-y-6">{features.map(([title, text]) => <div key={title} className="flex gap-4"><span className="mt-1 grid size-6 shrink-0 place-items-center rounded-full bg-emerald-100 text-emerald-700"><Check size={14} strokeWidth={2.5}/></span><div><h3 className="font-semibold text-emerald-950">{title}</h3><p className="mt-1.5 leading-6 text-emerald-950/53">{text}</p></div></div>)}</div>
        </div>
      </div>
    </section>
  );
}
