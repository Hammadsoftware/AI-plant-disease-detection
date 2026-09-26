import Image from "next/image";

export function UserMessage({ preview, filename }: { preview: string; filename: string }) {
  return <div className="ml-auto max-w-xl"><p className="mb-2 text-right text-xs font-medium text-emerald-950/40">You</p><div className="overflow-hidden rounded-[1.5rem] rounded-tr-md bg-emerald-100/70 p-2"><Image src={preview} alt={`Uploaded plant leaf: ${filename}`} width={1024} height={768} unoptimized className="max-h-[360px] w-full rounded-[1.15rem] object-contain"/></div><p className="mt-2 text-right text-xs text-emerald-950/38">Analyze this leaf</p></div>;
}
