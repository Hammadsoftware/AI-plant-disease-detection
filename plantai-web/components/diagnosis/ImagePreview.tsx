import { FileImage, X } from "lucide-react";
import Image from "next/image";
import { formatBytes } from "@/lib/utils";

interface ImagePreviewProps { preview: string; filename: string; fileSize: number; onRemove?: () => void; }

export function ImagePreview({ preview, filename, fileSize, onRemove }: ImagePreviewProps) {
  return <div className="overflow-hidden rounded-[1.6rem] border border-emerald-950/10 bg-white shadow-[0_16px_50px_rgba(8,63,47,.07)]"><div className="relative aspect-[16/9] max-h-[420px] bg-emerald-950/5"><Image src={preview} alt={`Selected plant leaf: ${filename}`} fill unoptimized className="object-contain"/>{onRemove && <button onClick={onRemove} aria-label="Remove selected image" className="absolute right-4 top-4 grid size-10 place-items-center rounded-full bg-white/90 text-emerald-950 shadow-lg backdrop-blur hover:bg-white"><X size={18}/></button>}</div><div className="flex items-center gap-3 border-t border-emerald-950/8 p-4"><span className="grid size-10 shrink-0 place-items-center rounded-xl bg-emerald-50 text-emerald-700"><FileImage size={18}/></span><div className="min-w-0"><p className="truncate text-sm font-semibold text-emerald-950">{filename}</p><p className="mt-0.5 text-xs text-emerald-950/42">{formatBytes(fileSize)}</p></div><span className="ml-auto rounded-full bg-emerald-50 px-3 py-1 text-[11px] font-semibold text-emerald-700">Ready</span></div></div>;
}
