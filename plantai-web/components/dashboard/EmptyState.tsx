import { ScanSearch } from "lucide-react";
import { ImageUploader } from "@/components/diagnosis/ImageUploader";

export function EmptyState({ onSelect, onCamera }: { onSelect: (file: File) => void; onCamera: () => void }) {
  return <div className="mx-auto flex w-full max-w-2xl flex-col items-center py-10 sm:py-16"><div className="relative mb-7"><span className="absolute inset-0 animate-ping rounded-[2rem] bg-emerald-200/35"/><span className="relative grid size-20 place-items-center rounded-[2rem] bg-emerald-950 text-lime-300 shadow-xl shadow-emerald-950/15"><ScanSearch size={31}/></span></div><ImageUploader onSelect={onSelect} onCamera={onCamera}/></div>;
}
