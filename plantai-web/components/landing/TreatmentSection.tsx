import { AlertCircle, ArrowUpRight, BadgeCheck, FlaskConical, Leaf } from "lucide-react";

export function TreatmentSection() {
  return (
    <section id="treatment" className="section-padding bg-white">
      <div className="page-shell grid items-center gap-14 lg:grid-cols-[.82fr_1.18fr]">
        <div><p className="section-kicker">Practical next steps</p><h2 className="section-title mt-4">Understand the next step.</h2><p className="mt-6 max-w-xl text-lg leading-8 text-emerald-950/60">When returned by the backend, PlantAI turns treatment guidance and pesticide information into a calm, easy-to-read response—without hardcoded recommendations.</p><a href="/dashboard" className="mt-8 inline-flex items-center gap-2 text-sm font-semibold text-emerald-700 hover:text-emerald-900">Begin with a leaf image <ArrowUpRight size={16}/></a></div>
        <div className="overflow-hidden rounded-[2rem] bg-[#e7f1e8] p-3 shadow-[0_30px_80px_rgba(8,63,47,.09)]">
          <div className="rounded-[1.55rem] bg-emerald-950 p-7 text-white sm:p-9">
            <div className="flex items-start justify-between gap-6"><div><p className="text-xs font-semibold uppercase tracking-[.15em] text-lime-300">Guidance panel</p><h3 className="mt-3 text-2xl font-semibold tracking-[-.035em]">A clearer path forward</h3></div><span className="grid size-12 shrink-0 place-items-center rounded-2xl bg-white/10 text-lime-300"><Leaf size={22}/></span></div>
            <div className="mt-9 grid gap-3 sm:grid-cols-3">
              <div className="rounded-2xl border border-white/10 bg-white/[.055] p-5"><BadgeCheck size={19} className="text-lime-300"/><p className="mt-8 text-sm font-medium">Management</p><p className="mt-2 text-xs leading-5 text-emerald-100/50">Cultural, physical, or biological guidance if provided.</p></div>
              <div className="rounded-2xl border border-white/10 bg-white/[.055] p-5"><FlaskConical size={19} className="text-lime-300"/><p className="mt-8 text-sm font-medium">Pesticides</p><p className="mt-2 text-xs leading-5 text-emerald-100/50">Products, ingredients, and status only when sourced.</p></div>
              <div className="rounded-2xl border border-white/10 bg-white/[.055] p-5"><AlertCircle size={19} className="text-lime-300"/><p className="mt-8 text-sm font-medium">Warnings</p><p className="mt-2 text-xs leading-5 text-emerald-100/50">Important caveats remain visible in the response.</p></div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
