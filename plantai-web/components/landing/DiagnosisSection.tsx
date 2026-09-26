"use client";

import { motion } from "framer-motion";
import { FileImage, Microscope, SearchCheck, ShieldCheck, Stethoscope } from "lucide-react";

const flow = [
  { label: "Leaf image", icon: FileImage },
  { label: "AI vision model", icon: Microscope },
  { label: "Disease identification", icon: SearchCheck },
  { label: "Evidence research", icon: ShieldCheck },
  { label: "Treatment guidance", icon: Stethoscope },
];

export function DiagnosisSection() {
  return (
    <section id="diagnosis" className="section-padding bg-emerald-950 text-white">
      <div className="page-shell">
        <div className="grid gap-14 lg:grid-cols-[.78fr_1.22fr] lg:items-end">
          <div><p className="section-kicker text-lime-300">Inside the analysis</p><h2 className="section-title mt-4 text-white">From leaf image to AI diagnosis.</h2><p className="mt-6 max-w-lg text-lg leading-8 text-emerald-100/65">One clear image moves through a deliberate pipeline—from visual classification to optional research and actionable context.</p></div>
          <div className="relative grid gap-3 sm:grid-cols-5">
            <motion.div className="absolute left-[10%] right-[10%] top-8 hidden h-px origin-left bg-gradient-to-r from-emerald-500 via-lime-300 to-emerald-500 sm:block" initial={{ scaleX: 0 }} whileInView={{ scaleX: 1 }} viewport={{ once: true }} transition={{ duration: 1.2 }} />
            {flow.map(({ label, icon: Icon }, index) => (
              <div key={label} className="relative z-10 flex items-center gap-4 rounded-2xl border border-white/10 bg-white/[.055] p-4 backdrop-blur-sm sm:block sm:border-0 sm:bg-transparent sm:p-0 sm:text-center">
                <span className="grid size-16 shrink-0 place-items-center rounded-2xl border border-white/15 bg-emerald-900 text-lime-300 shadow-lg sm:mx-auto"><Icon size={23} /></span>
                <p className="text-sm font-medium text-emerald-50 sm:mt-4">{label}</p><span className="ml-auto text-xs text-white/25 sm:hidden">0{index + 1}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
