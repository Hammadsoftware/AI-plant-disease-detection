"use client";

import { RotateCcw, Square } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { AssistantMessage } from "./AssistantMessage";

interface StreamedResponseProps {
  content: string;
  streaming: boolean;
  stopped: boolean;
  onStop: () => void;
  onRetry: () => void;
}

export function StreamedResponse({ content, streaming, stopped, onStop, onRetry }: StreamedResponseProps) {
  return <AssistantMessage><div className="rounded-[1.5rem] border border-emerald-950/9 bg-white px-5 py-6 shadow-[0_16px_50px_rgba(8,63,47,.06)] sm:px-7"><div className="stream-markdown text-[15px] leading-7 text-emerald-950/76"><ReactMarkdown components={{
    h1: ({ children }) => <h2 className="mb-3 mt-7 text-xl font-semibold tracking-[-.025em] text-emerald-950 first:mt-0">{children}</h2>,
    h2: ({ children }) => <h2 className="mb-3 mt-7 text-lg font-semibold tracking-[-.02em] text-emerald-950 first:mt-0">{children}</h2>,
    h3: ({ children }) => <h3 className="mb-2 mt-5 font-semibold text-emerald-900">{children}</h3>,
    p: ({ children }) => <p className="my-3 first:mt-0 last:mb-0">{children}</p>,
    ul: ({ children }) => <ul className="my-3 list-disc space-y-1.5 pl-5 marker:text-emerald-500">{children}</ul>,
    ol: ({ children }) => <ol className="my-3 list-decimal space-y-1.5 pl-5 marker:font-semibold marker:text-emerald-700">{children}</ol>,
    strong: ({ children }) => <strong className="font-semibold text-emerald-950">{children}</strong>,
    a: ({ href, children }) => <a href={href} target="_blank" rel="noreferrer" className="font-medium text-emerald-700 underline decoration-emerald-300 underline-offset-4 hover:text-emerald-900">{children}</a>,
  }}>{content}</ReactMarkdown>{streaming && <span className="ml-0.5 inline-block animate-pulse font-semibold text-emerald-600" aria-label="PlantAI is generating">▌</span>}</div>{streaming && <button type="button" onClick={onStop} className="mt-5 inline-flex items-center gap-2 rounded-full border border-emerald-950/12 bg-white px-4 py-2 text-xs font-semibold text-emerald-950 transition hover:border-emerald-700/30 hover:bg-emerald-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600"><Square size={12} fill="currentColor"/>Stop generating</button>}{stopped && <div className="mt-5 flex items-center gap-3 border-t border-emerald-950/8 pt-4"><span className="text-xs text-emerald-950/48">Generation stopped</span><button type="button" onClick={onRetry} className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-700 hover:text-emerald-950"><RotateCcw size={13}/>Retry</button></div>}</div></AssistantMessage>;
}
