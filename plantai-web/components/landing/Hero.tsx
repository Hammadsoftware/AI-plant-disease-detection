"use client";

import Image from "next/image";
import Link from "next/link";
import { ArrowRight, CheckCircle2, ScanLine, Sparkles } from "lucide-react";
import { motion } from "framer-motion";

export function Hero() {
  return (
    <section className="relative min-h-[860px] bg-[#f7faf5] pb-20 pt-36 lg:min-h-[900px] lg:pt-40">
      <div className="hero-grid absolute inset-0 opacity-45" aria-hidden="true" />
      <div className="absolute left-[-12rem] top-40 size-[30rem] rounded-full bg-emerald-200/30 blur-3xl" aria-hidden="true" />
      <div className="page-shell relative grid items-center gap-16 lg:grid-cols-[1.02fr_.98fr]">
        <motion.div initial={false} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.65 }}>
          <div className="eyebrow"><Sparkles size={14} /> Intelligent plant health</div>
          <h1 className="mt-7 max-w-3xl text-balance text-[clamp(3.4rem,7vw,6.65rem)] font-medium leading-[.93] tracking-[-0.065em] text-emerald-950">
            Know what your plant needs.
          </h1>
          <p className="mt-8 max-w-xl text-pretty text-lg leading-8 text-emerald-950/63 sm:text-xl">
            AI-powered plant disease diagnosis with evidence-backed research and treatment guidance.
          </p>
          <div className="mt-10 flex flex-col gap-3 sm:flex-row">
            <Link href="/dashboard" className="button-primary justify-center px-6 py-4 text-base">Start Diagnosis <ArrowRight size={18} /></Link>
            <Link href="#how-it-works" className="button-secondary justify-center px-6 py-4 text-base">How It Works</Link>
          </div>
          <div className="mt-9 flex flex-wrap gap-x-6 gap-y-3 text-sm text-emerald-950/55">
            <span className="inline-flex items-center gap-2"><CheckCircle2 size={16} className="text-emerald-600" /> Clear, structured results</span>
            <span className="inline-flex items-center gap-2"><CheckCircle2 size={16} className="text-emerald-600" /> Your image, analyzed on demand</span>
          </div>
        </motion.div>

        <motion.div className="relative mx-auto w-full max-w-[580px]" initial={false} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.8, delay: 0.1 }}>
          <div className="relative aspect-[4/5] overflow-hidden rounded-[2.25rem] border border-white/70 bg-emerald-900 shadow-[0_35px_90px_rgba(8,63,47,.2)]">
            <Image src="/images/leaf-diagnostic-hero.png" alt="A healthy green leaf under a subtle AI scanning light" fill priority sizes="(max-width: 1024px) 90vw, 46vw" className="object-cover" />
            <div className="absolute inset-x-8 top-[28%] h-px bg-gradient-to-r from-transparent via-lime-200 to-transparent shadow-[0_0_28px_6px_rgba(190,242,100,.6)] animate-scan" aria-hidden="true" />
            <div className="absolute inset-0 bg-gradient-to-t from-emerald-950/35 via-transparent to-white/5" aria-hidden="true" />
            <div className="absolute left-5 top-5 rounded-2xl border border-white/35 bg-white/88 p-4 shadow-xl backdrop-blur-xl sm:left-8 sm:top-8">
              <div className="flex items-center gap-3">
                <span className="grid size-10 place-items-center rounded-xl bg-emerald-950 text-lime-300"><ScanLine size={19} /></span>
                <div><p className="text-xs font-medium uppercase tracking-[.13em] text-emerald-800/55">Plant Disease AI</p><p className="mt-1 text-sm font-semibold text-emerald-950">Analyzing leaf</p></div>
                <span className="ml-3 size-2.5 animate-pulse rounded-full bg-emerald-500" />
              </div>
            </div>
          </div>
          <div className="absolute -bottom-6 -left-4 hidden w-56 rounded-2xl border border-emerald-900/10 bg-[#fcfdf9]/92 p-4 shadow-2xl backdrop-blur-xl sm:block">
            <div className="mb-3 flex items-center justify-between text-xs font-medium text-emerald-950/55"><span>Visual pattern</span><span className="text-emerald-700">Scanning</span></div>
            <div className="space-y-2"><span className="block h-1.5 w-full overflow-hidden rounded-full bg-emerald-100"><motion.span className="block h-full bg-emerald-600" animate={{ width: ["18%", "90%", "40%"] }} transition={{ duration: 3.2, repeat: Infinity }} /></span><span className="block h-1.5 w-3/4 rounded-full bg-emerald-100" /></div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
