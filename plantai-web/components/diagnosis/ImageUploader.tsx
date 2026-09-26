"use client";

import { Camera, ImagePlus, UploadCloud } from "lucide-react";
import { useRef, useState } from "react";

interface ImageUploaderProps {
  onSelect: (file: File) => void;
  onCamera: () => void;
  compact?: boolean;
}

export function ImageUploader({ onSelect, onCamera, compact = false }: ImageUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const choose = (files: FileList | null) => {
    const file = files?.[0];
    if (file) onSelect(file);
  };

  return (
    <div
      className={`relative rounded-[1.6rem] border border-dashed transition ${dragging ? "border-emerald-500 bg-emerald-50" : "border-emerald-950/15 bg-white hover:border-emerald-700/30"} ${compact ? "p-4" : "p-8 sm:p-10"}`}
      onDragEnter={(event) => { event.preventDefault(); setDragging(true); }}
      onDragOver={(event) => event.preventDefault()}
      onDragLeave={(event) => { if (!event.currentTarget.contains(event.relatedTarget as Node)) setDragging(false); }}
      onDrop={(event) => { event.preventDefault(); setDragging(false); choose(event.dataTransfer.files); }}
    >
      <input ref={inputRef} type="file" accept="image/jpeg,image/png,image/webp" className="sr-only" onChange={(event) => { choose(event.target.files); event.currentTarget.value = ""; }} aria-label="Choose a plant leaf image" />
      <div className="mx-auto flex max-w-md flex-col items-center text-center">
        <span className={`grid place-items-center rounded-[1.4rem] bg-emerald-50 text-emerald-700 ${compact ? "size-12" : "size-16"}`}><ImagePlus size={compact ? 22 : 27} /></span>
        {!compact && <><h2 className="mt-6 text-2xl font-semibold tracking-[-.035em] text-emerald-950">Upload a plant leaf to begin</h2><p className="mt-3 text-sm leading-6 text-emerald-950/52">Upload a clear photo and let PlantAI analyze it. You can also drag and drop it here.</p></>}
        <div className={`flex w-full flex-col gap-2 sm:flex-row sm:justify-center ${compact ? "mt-3" : "mt-7"}`}>
          <button type="button" onClick={() => inputRef.current?.click()} className="button-primary justify-center"><UploadCloud size={17} /> Upload Image</button>
          <button type="button" onClick={onCamera} className="button-secondary justify-center"><Camera size={17} /> Scan with Camera</button>
        </div>
        {!compact && <p className="mt-5 text-[11px] font-semibold uppercase tracking-[.14em] text-emerald-950/35">JPG · JPEG · PNG · WEBP · up to 10 MB</p>}
      </div>
    </div>
  );
}
