"use client";

import { ArrowRight, ImagePlus, LoaderCircle, ShieldCheck } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { CameraCapture } from "@/components/diagnosis/CameraCapture";
import { DiagnosisConversation } from "@/components/diagnosis/DiagnosisConversation";
import { ImagePreview } from "@/components/diagnosis/ImagePreview";
import { ImageUploader } from "@/components/diagnosis/ImageUploader";
import { checkHealth, diagnoseLeafStream, PlantApiError } from "@/lib/api";
import { loadHistory, saveHistory } from "@/lib/storage";
import type { DiagnosisResponse, HistoryItem, ServiceStatus } from "@/lib/types";
import { fileToDataUrl, optimizeImage, validateImageFile } from "@/lib/utils";
import { DashboardHeader } from "./DashboardHeader";
import { EmptyState } from "./EmptyState";
import { Sidebar } from "./Sidebar";

interface SelectedImage { file: File | null; preview: string; filename: string; size: number; }

export function Dashboard() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [cameraOpen, setCameraOpen] = useState(false);
  const [selected, setSelected] = useState<SelectedImage | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [phaseMessage, setPhaseMessage] = useState("Analyzing your plant leaf...");
  const [streamedContent, setStreamedContent] = useState("");
  const [stopped, setStopped] = useState(false);
  const [result, setResult] = useState<DiagnosisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectionError, setSelectionError] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [serviceStatus, setServiceStatus] = useState<ServiceStatus>("checking");
  const uploadFallbackRef = useRef<HTMLInputElement>(null);
  const conversationEndRef = useRef<HTMLDivElement>(null);
  const activeRequestRef = useRef<AbortController | null>(null);
  const stopRequestedRef = useRef(false);

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => setHistory(loadHistory()));
    return () => window.cancelAnimationFrame(frame);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    checkHealth(controller.signal)
      .then((health) => setServiceStatus(health.status === "ok" && health.model_loaded ? "online" : "unavailable"))
      .catch(() => setServiceStatus("unavailable"));
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (submitted) conversationEndRef.current?.scrollIntoView({ block: "end" });
  }, [submitted, loading, result, error, streamedContent]);

  useEffect(() => () => activeRequestRef.current?.abort(), []);

  const newScan = useCallback(() => {
    activeRequestRef.current?.abort(); activeRequestRef.current = null; stopRequestedRef.current = false;
    setSelected(null); setSubmitted(false); setLoading(false); setPhaseMessage("Analyzing your plant leaf..."); setStreamedContent(""); setStopped(false); setResult(null); setError(null); setSelectionError(null); setSidebarOpen(false);
  }, []);

  const selectFile = useCallback(async (incoming: File) => {
    setSelectionError(null);
    const validation = validateImageFile(incoming);
    if (validation) { setSelectionError(validation); return; }
    try {
      const file = await optimizeImage(incoming);
      const preview = await fileToDataUrl(file);
      setSelected({ file, preview, filename: file.name, size: file.size });
      setSubmitted(false); setPhaseMessage("Analyzing your plant leaf..."); setStreamedContent(""); setStopped(false); setResult(null); setError(null); setSidebarOpen(false);
    } catch {
      setSelectionError("PlantAI couldn’t prepare this image. Please choose another photo.");
    }
  }, []);

  const analyze = useCallback(async () => {
    if (!selected?.file || loading) return;
    const controller = new AbortController();
    activeRequestRef.current?.abort(); activeRequestRef.current = controller; stopRequestedRef.current = false;
    setSubmitted(true); setLoading(true); setPhaseMessage("Analyzing your plant leaf..."); setStreamedContent(""); setStopped(false); setResult(null); setError(null);
    try {
      const response = await diagnoseLeafStream(selected.file, {
        onPhase: (_phase, message) => setPhaseMessage(message),
        onToken: (token) => setStreamedContent((current) => current + token),
        onMetadata: (metadata) => setResult(metadata),
      }, controller.signal);
      if (response.result) {
        setResult(response.result);
        const item: HistoryItem = {
          id: crypto.randomUUID(), timestamp: new Date().toISOString(), imagePreview: selected.preview,
          filename: selected.filename, fileSize: selected.size, disease: response.result.diagnosis.disease,
          confidence: response.result.diagnosis.confidence, result: response.result, streamedContent: response.content,
        };
        setHistory((current) => saveHistory([item, ...current]));
      }
    } catch (cause) {
      const aborted = cause instanceof DOMException && cause.name === "AbortError";
      if (aborted && stopRequestedRef.current) {
        setStopped(true);
      } else if (!aborted) {
        const message = cause instanceof PlantApiError && cause.status !== null
          ? cause.message
          : "Something went wrong while generating the diagnosis.";
        setError(message);
      }
    } finally {
      if (activeRequestRef.current === controller) activeRequestRef.current = null;
      setLoading(false);
    }
  }, [loading, selected]);

  const stopGeneration = useCallback(() => {
    stopRequestedRef.current = true;
    activeRequestRef.current?.abort();
    setLoading(false);
    setStopped(true);
  }, []);

  const restoreHistory = (item: HistoryItem) => {
    setSelected({ file: null, preview: item.imagePreview, filename: item.filename, size: item.fileSize });
    setSubmitted(true); setPhaseMessage("Analyzing your plant leaf..."); setStreamedContent(item.streamedContent ?? ""); setStopped(false); setResult(item.result); setError(null); setLoading(false); setSidebarOpen(false);
  };

  const deleteHistory = (id: string) => setHistory((current) => saveHistory(current.filter((item) => item.id !== id)));

  return <main className="flex h-dvh overflow-hidden bg-[#f4f7f2]">
    <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} onNewScan={newScan} history={history} onSelectHistory={restoreHistory} onDeleteHistory={deleteHistory} serviceStatus={serviceStatus}/>
    <div className="flex min-w-0 flex-1 flex-col">
      <DashboardHeader onMenu={() => setSidebarOpen(true)} onNewScan={newScan} status={serviceStatus}/>
      <section className="min-h-0 flex-1 overflow-y-auto" aria-label="Diagnosis conversation">
        <div className="mx-auto w-full max-w-4xl px-4 py-6 sm:px-7 sm:py-9">
          {!selected && <EmptyState onSelect={(file) => void selectFile(file)} onCamera={() => setCameraOpen(true)}/>} 
          {selectionError && <div role="alert" className="mx-auto mb-5 max-w-2xl rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{selectionError}</div>}
          {selected && !submitted && <div className="mx-auto max-w-2xl space-y-4"><div><p className="text-xs font-bold uppercase tracking-[.14em] text-emerald-700">Image ready</p><h1 className="mt-2 text-2xl font-semibold tracking-[-.04em] text-emerald-950">Review before analysis</h1><p className="mt-2 text-sm leading-6 text-emerald-950/50">Your image stays here until you ask PlantAI to analyze it.</p></div><ImagePreview preview={selected.preview} filename={selected.filename} fileSize={selected.size} onRemove={newScan}/><ImageUploader onSelect={(file) => void selectFile(file)} onCamera={() => setCameraOpen(true)} compact/></div>}
          {selected && submitted && <DiagnosisConversation preview={selected.preview} filename={selected.filename} loading={loading} phaseMessage={phaseMessage} streamedContent={streamedContent} stopped={stopped} result={result} error={error} onStop={stopGeneration} onRetry={() => void analyze()} onNewScan={newScan}/>} 
          <div ref={conversationEndRef}/>
        </div>
      </section>
      {selected && !submitted && <div className="shrink-0 border-t border-emerald-950/8 bg-white/92 px-4 py-3 backdrop-blur-xl sm:px-7 sm:py-4"><div className="mx-auto flex max-w-4xl items-center justify-between gap-4"><div className="hidden items-center gap-2 text-xs text-emerald-950/42 sm:flex"><ShieldCheck size={15} className="text-emerald-600"/>Analysis starts only when you continue.</div><button onClick={() => void analyze()} disabled={!selected.file || loading} className="ml-auto inline-flex w-full items-center justify-center gap-2 rounded-full bg-emerald-950 px-6 py-3.5 text-sm font-semibold text-white shadow-lg shadow-emerald-950/15 transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto">{loading ? <LoaderCircle size={17} className="animate-spin"/> : <ImagePlus size={17} className="text-lime-300"/>}Analyze Leaf <ArrowRight size={16}/></button></div></div>}
    </div>
    <input ref={uploadFallbackRef} type="file" accept="image/jpeg,image/png,image/webp" className="sr-only" onChange={(event) => { const file = event.target.files?.[0]; if (file) void selectFile(file); event.currentTarget.value = ""; }} aria-label="Upload a plant leaf photo"/>
    <CameraCapture open={cameraOpen} onClose={() => setCameraOpen(false)} onUsePhoto={(file) => void selectFile(file)} onUploadFallback={() => uploadFallbackRef.current?.click()}/>
  </main>;
}
