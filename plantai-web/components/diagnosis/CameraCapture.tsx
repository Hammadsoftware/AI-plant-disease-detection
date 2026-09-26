"use client";

import { Camera, Check, RefreshCcw, Upload, X } from "lucide-react";
import Image from "next/image";
import { useCallback, useEffect, useRef, useState } from "react";

interface CameraCaptureProps {
  open: boolean;
  onClose: () => void;
  onUsePhoto: (file: File) => void;
  onUploadFallback: () => void;
}

export function CameraCapture({ open, onClose, onUsePhoto, onUploadFallback }: CameraCaptureProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [capture, setCapture] = useState<string | null>(null);
  const [cameraError, setCameraError] = useState<string | null>(null);

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }, []);

  useEffect(() => {
    if (!open) return;
    let active = true;
    const start = async () => {
      setCameraError(null);
      if (!navigator.mediaDevices?.getUserMedia) {
        setCameraError("Camera access isn’t supported in this browser.");
        return;
      }
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: "environment" } }, audio: false });
        if (!active) { stream.getTracks().forEach((track) => track.stop()); return; }
        streamRef.current = stream;
        if (videoRef.current) videoRef.current.srcObject = stream;
      } catch {
        setCameraError("Camera access is unavailable. You can upload a photo instead.");
      }
    };
    void start();
    return () => { active = false; stopCamera(); setCapture(null); };
  }, [open, stopCamera]);

  const takePhoto = () => {
    const video = videoRef.current;
    if (!video?.videoWidth) return;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d")?.drawImage(video, 0, 0);
    setCapture(canvas.toDataURL("image/jpeg", 0.92));
  };

  const acceptPhoto = async () => {
    if (!capture) return;
    const response = await fetch(capture);
    const blob = await response.blob();
    onUsePhoto(new File([blob], `plant-leaf-${Date.now()}.jpg`, { type: "image/jpeg" }));
    onClose();
  };

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-[100] grid place-items-center bg-emerald-950/65 p-4 backdrop-blur-sm" role="dialog" aria-modal="true" aria-labelledby="camera-title" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <div className="w-full max-w-2xl overflow-hidden rounded-[1.75rem] bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-emerald-950/8 px-5 py-4"><div><h2 id="camera-title" className="font-semibold text-emerald-950">Scan with camera</h2><p className="mt-0.5 text-xs text-emerald-950/45">Keep the leaf centered and in clear light.</p></div><button onClick={onClose} aria-label="Close camera" className="grid size-10 place-items-center rounded-xl text-emerald-950/55 hover:bg-emerald-50"><X size={20}/></button></div>
        <div className="relative aspect-[4/3] bg-emerald-950">
          {cameraError ? <div className="absolute inset-0 grid place-items-center p-8 text-center"><div><Camera className="mx-auto text-emerald-300"/><p className="mt-4 text-sm text-white/70">{cameraError}</p><button onClick={() => { onClose(); onUploadFallback(); }} className="mt-6 inline-flex items-center gap-2 rounded-full bg-white px-5 py-3 text-sm font-semibold text-emerald-950"><Upload size={17}/> Upload a photo</button></div></div> : <><video ref={videoRef} autoPlay muted playsInline className={`size-full object-cover ${capture ? "invisible" : ""}`} aria-label="Live camera preview" />{capture && <Image src={capture} alt="Captured plant leaf preview" fill unoptimized className="object-contain" />}</>}
          {!cameraError && !capture && <div className="pointer-events-none absolute inset-[12%] rounded-[1.5rem] border border-lime-300/55"><span className="absolute left-1/2 top-0 h-px w-4/5 -translate-x-1/2 bg-lime-300/80 animate-scan" /></div>}
        </div>
        {!cameraError && <div className="flex justify-center gap-3 p-5">{capture ? <><button onClick={() => setCapture(null)} className="button-secondary"><RefreshCcw size={17}/> Retake</button><button onClick={() => void acceptPhoto()} className="button-primary"><Check size={17}/> Use photo</button></> : <button onClick={takePhoto} className="button-primary px-7"><Camera size={18}/> Capture</button>}</div>}
      </div>
    </div>
  );
}
