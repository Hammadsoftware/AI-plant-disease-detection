import type { DiagnosisResponse } from "@/lib/types";
import { DiagnosisResult } from "./DiagnosisResult";
import { ErrorState } from "./ErrorState";
import { LoadingState } from "./LoadingState";
import { UserMessage } from "./UserMessage";

interface DiagnosisConversationProps { preview: string; filename: string; loading: boolean; result: DiagnosisResponse | null; error: string | null; onRetry: () => void; onNewScan: () => void; }

export function DiagnosisConversation({ preview, filename, loading, result, error, onRetry, onNewScan }: DiagnosisConversationProps) {
  return <div className="space-y-10 py-4"><UserMessage preview={preview} filename={filename}/>{loading && <LoadingState message="Analyzing your plant leaf..."/>} {error && <ErrorState message={error} onRetry={onRetry} onNewScan={onNewScan}/>} {result && !loading && !error && <DiagnosisResult result={result}/>}</div>;
}
