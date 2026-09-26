import Link from "next/link";
import { ArrowRight, Sparkles } from "lucide-react";

export function CTA() {
  return (
    <section className="px-4 pb-6 pt-12 sm:px-6 lg:px-8">
      <div className="relative mx-auto max-w-[1400px] overflow-hidden rounded-[2rem] bg-emerald-950 px-6 py-20 text-center text-white sm:px-10 sm:py-24">
        <div className="absolute inset-0 opacity-20 hero-grid" aria-hidden="true"/><div className="absolute left-1/2 top-0 h-40 w-[34rem] -translate-x-1/2 rounded-full bg-emerald-400/20 blur-3xl" aria-hidden="true"/>
        <div className="relative"><Sparkles className="mx-auto text-lime-300" size={25}/><h2 className="mx-auto mt-6 max-w-3xl text-balance text-4xl font-medium tracking-[-.05em] sm:text-6xl">Ready to check your plant?</h2><p className="mx-auto mt-5 max-w-lg text-emerald-100/60">Upload a clear leaf image and begin a focused AI-assisted diagnosis.</p><Link href="/dashboard" className="mt-9 inline-flex items-center gap-2 rounded-full bg-lime-300 px-6 py-3.5 text-sm font-bold text-emerald-950 transition hover:bg-lime-200">Start Diagnosis <ArrowRight size={17}/></Link></div>
      </div>
    </section>
  );
}
