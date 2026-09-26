import { AlertCircle, ArrowUpRight, BadgeCheck, Beaker, BookOpen, CircleHelp, FlaskConical, Info, Leaf, ShieldCheck } from "lucide-react";
import type { DiagnosisResponse, ResearchSource } from "@/lib/types";
import { formatConfidence } from "@/lib/utils";
import { AssistantMessage } from "./AssistantMessage";

function ListSection({ title, items, icon: Icon }: { title: string; items: string[]; icon: typeof Leaf }) {
  if (!items.length) return null;
  return <section className="border-t border-emerald-950/8 pt-7"><h3 className="flex items-center gap-2 text-base font-semibold text-emerald-950"><Icon size={18} className="text-emerald-700"/>{title}</h3><ul className="mt-4 space-y-3">{items.map((item, index) => <li key={`${title}-${index}`} className="flex gap-3 text-sm leading-6 text-emerald-950/65"><span className="mt-2 size-1.5 shrink-0 rounded-full bg-emerald-500"/>{item}</li>)}</ul></section>;
}

function Sources({ sources }: { sources: ResearchSource[] }) {
  const unique = Array.from(new Map(sources.map((source) => [source.url, source])).values());
  if (!unique.length) return null;
  return <section className="border-t border-emerald-950/8 pt-7"><h3 className="flex items-center gap-2 text-base font-semibold text-emerald-950"><BookOpen size={18} className="text-emerald-700"/>Supporting sources</h3><div className="mt-4 grid gap-3 sm:grid-cols-2">{unique.map((source) => <a key={source.url} href={source.url} target="_blank" rel="noreferrer" className="group rounded-2xl border border-emerald-950/9 bg-[#fafcf9] p-4 transition hover:border-emerald-600/30 hover:bg-emerald-50/50"><div className="flex items-start gap-3"><span className="grid size-9 shrink-0 place-items-center rounded-xl bg-white text-emerald-700 shadow-sm"><ArrowUpRight size={16}/></span><div className="min-w-0"><p className="line-clamp-2 text-sm font-semibold leading-5 text-emerald-950 group-hover:text-emerald-700">{source.title}</p><p className="mt-1 truncate text-xs text-emerald-950/42">{source.source} · {source.source_type.replaceAll("_", " ")}</p></div></div></a>)}</div></section>;
}

export function DiagnosisResult({ result }: { result: DiagnosisResponse }) {
  const explanation = result.explanation;
  const management = explanation?.management;
  const evidenceClaims = result.research?.evidence.claims ?? [];
  const sources = [
    ...(explanation?.sources ?? []),
    ...(result.research?.evidence.sources ?? []),
    ...(result.research?.disease.sources ?? []),
    ...(result.research?.treatment.sources ?? []),
    ...(result.research?.pesticide.sources ?? []),
  ];
  const treatments = management ? [...management.cultural, ...management.biological, ...management.physical, ...management.chemical] : [];
  const warnings = Array.from(new Set([
    ...(result.warnings ?? []),
    ...(explanation?.warnings ?? []),
    ...(result.research?.evidence.warnings ?? []),
    ...(result.research?.evidence.disagreements ?? []),
    ...(result.explanation_error ? ["Extended explanation was unavailable for this scan."] : []),
  ]));
  return <AssistantMessage><article className="rounded-[1.65rem] border border-emerald-950/9 bg-white p-5 shadow-[0_18px_60px_rgba(8,63,47,.065)] sm:p-7">
    <section><div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"><div><p className="text-xs font-bold uppercase tracking-[.14em] text-emerald-700">Diagnosis</p><h2 className="mt-2 text-2xl font-semibold tracking-[-.04em] text-emerald-950 sm:text-3xl">{result.diagnosis.disease}</h2><p className="mt-2 text-sm text-emerald-950/45">{result.diagnosis.class_name}</p></div><span className={`inline-flex w-fit items-center gap-2 rounded-full px-3.5 py-2 text-xs font-semibold ${result.diagnosis.is_uncertain ? "bg-amber-50 text-amber-800" : "bg-emerald-50 text-emerald-700"}`}><BadgeCheck size={15}/>{formatConfidence(result.diagnosis.confidence)}</span></div>{result.diagnosis.is_uncertain && <div className="mt-5 flex gap-3 rounded-2xl bg-amber-50 p-4 text-sm leading-6 text-amber-900/75"><CircleHelp size={18} className="mt-0.5 shrink-0"/><p>This prediction is marked uncertain by the model. Consider a clearer image or local expert confirmation.</p></div>}</section>
    {explanation && <section className="mt-7 border-t border-emerald-950/8 pt-7"><h3 className="flex items-center gap-2 text-base font-semibold text-emerald-950"><Info size={18} className="text-emerald-700"/>Analysis</h3><p className="mt-4 text-[15px] leading-7 text-emerald-950/67">{explanation.summary}</p>{explanation.diagnosis.confidence_note && <p className="mt-3 rounded-xl bg-emerald-50/70 px-4 py-3 text-sm leading-6 text-emerald-900/65">{explanation.diagnosis.confidence_note}</p>}</section>}
    <ListSection title="Visible symptoms" items={explanation?.symptoms ?? []} icon={Leaf}/><ListSection title="Possible causes" items={explanation?.possible_causes ?? []} icon={Beaker}/><ListSection title="Treatment & management" items={treatments} icon={ShieldCheck}/><ListSection title="Prevention" items={explanation?.prevention ?? []} icon={BadgeCheck}/><ListSection title="Recommendations" items={explanation?.recommendations ?? []} icon={Leaf}/>
    {!!evidenceClaims.length && <section className="border-t border-emerald-950/8 pt-7"><h3 className="flex items-center gap-2 text-base font-semibold text-emerald-950"><BookOpen size={18} className="text-emerald-700"/>Research evidence</h3><div className="mt-4 space-y-3">{evidenceClaims.map((claim, index) => <div key={`${claim.category}-${index}`} className="rounded-2xl bg-[#f5f8f3] p-4"><div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[.12em] text-emerald-700">{claim.authoritative && <ShieldCheck size={13}/>} {claim.category}</div><p className="mt-2 text-sm leading-6 text-emerald-950/65">{claim.claim}</p></div>)}</div></section>}
    {!!explanation?.pesticides.length && <section className="border-t border-emerald-950/8 pt-7"><h3 className="flex items-center gap-2 text-base font-semibold text-emerald-950"><FlaskConical size={18} className="text-emerald-700"/>Pesticide information</h3><div className="mt-4 space-y-3">{explanation.pesticides.map((item) => <div key={`${item.product_name}-${item.active_ingredient}`} className="rounded-2xl border border-emerald-950/9 p-5"><div className="flex flex-wrap items-center gap-2"><p className="font-semibold text-emerald-950">{item.product_name}</p><span className={`rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide ${item.registration_status === "verified" ? "bg-emerald-50 text-emerald-700" : "bg-stone-100 text-stone-600"}`}>{item.registration_status}</span></div><p className="mt-1 text-xs text-emerald-950/45">Active ingredient: {item.active_ingredient} · {item.pesticide_type}</p><p className="mt-3 text-sm leading-6 text-emerald-950/65">{item.application_information}</p></div>)}</div></section>}
    <ListSection title="Important notes" items={warnings} icon={AlertCircle}/><Sources sources={sources}/>
    {!!result.diagnosis.top_predictions.length && <details className="mt-7 border-t border-emerald-950/8 pt-5"><summary className="cursor-pointer text-sm font-semibold text-emerald-800">Model information</summary><div className="mt-4 space-y-2">{result.diagnosis.top_predictions.map((prediction) => <div key={prediction.class_name} className="flex items-center justify-between gap-4 rounded-xl bg-stone-50 px-4 py-3 text-sm"><span className="truncate text-emerald-950/65">{prediction.disease}</span><span className="shrink-0 font-semibold text-emerald-800">{Math.round(prediction.confidence * 100)}%</span></div>)}</div></details>}
  </article></AssistantMessage>;
}
