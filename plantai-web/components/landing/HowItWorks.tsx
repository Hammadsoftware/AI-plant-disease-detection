import { BrainCircuit, Camera, MessageSquareText } from "lucide-react";

const steps = [
  { number: "01", title: "Upload", text: "Upload a clear image of a plant leaf.", icon: Camera },
  { number: "02", title: "Analyze", text: "Our AI analyzes visual disease patterns.", icon: BrainCircuit },
  { number: "03", title: "Understand", text: "Receive diagnosis, evidence, and treatment guidance.", icon: MessageSquareText },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="section-padding bg-white">
      <div className="page-shell">
        <div className="max-w-2xl"><p className="section-kicker">A simple diagnostic flow</p><h2 className="section-title mt-4">Clarity in three thoughtful steps.</h2></div>
        <div className="mt-14 grid gap-5 md:grid-cols-3">
          {steps.map(({ number, title, text, icon: Icon }) => (
            <article key={number} className="group rounded-[1.5rem] border border-emerald-950/9 bg-[#fafcf8] p-7 transition duration-300 hover:-translate-y-1 hover:border-emerald-700/20 hover:shadow-[0_24px_60px_rgba(10,70,52,.09)] sm:p-8">
              <div className="flex items-center justify-between"><span className="font-mono text-sm text-emerald-700">{number}</span><span className="grid size-11 place-items-center rounded-2xl bg-emerald-100/70 text-emerald-800"><Icon size={20} /></span></div>
              <h3 className="mt-14 text-2xl font-semibold tracking-[-.035em] text-emerald-950">{title}</h3><p className="mt-3 leading-7 text-emerald-950/58">{text}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
