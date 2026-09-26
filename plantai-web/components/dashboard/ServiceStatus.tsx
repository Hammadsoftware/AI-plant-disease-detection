import type { ServiceStatus as Status } from "@/lib/types";

export function ServiceStatus({ status, compact = false }: { status: Status; compact?: boolean }) {
  const label = status === "online" ? "AI Service Online" : status === "idle" ? "Ready to analyze" : "AI Service Unavailable";
  const color = status === "online" ? "bg-emerald-500" : status === "idle" ? "bg-stone-400" : "bg-red-500";
  return <div className={`flex items-center gap-2 ${compact ? "text-xs" : "text-[11px]"} font-medium text-emerald-950/52`}><span className={`size-2 rounded-full ${color}`} aria-hidden="true"/><span>{label}</span></div>;
}
