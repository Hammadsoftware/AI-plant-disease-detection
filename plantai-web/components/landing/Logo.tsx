import Link from "next/link";
import { Sprout } from "lucide-react";

export function Logo({ inverse = false }: { inverse?: boolean }) {
  return (
    <Link href="/" aria-label="PlantAI home" className={`inline-flex items-center gap-2 text-lg font-semibold tracking-[-0.03em] ${inverse ? "text-white" : "text-emerald-950"}`}>
      <span className={`grid size-9 place-items-center rounded-xl ${inverse ? "bg-white/12 text-lime-300" : "bg-emerald-950 text-lime-300"}`}>
        <Sprout size={18} strokeWidth={2.2} aria-hidden="true" />
      </span>
      <span>Plant<span className="text-emerald-600">AI</span></span>
    </Link>
  );
}
