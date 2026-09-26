import type { DiagnosisResponse } from "@/lib/types";
import { DiagnosisResult } from "./DiagnosisResult";
import { ErrorState } from "./ErrorState";
import { LoadingState } from "./LoadingState";
import { StreamedResponse } from "./StreamedResponse";
import { UserMessage } from "./UserMessage";

interface DiagnosisConversationProps { preview: string; filename: string; loading: boolean; phaseMessage: string; streamedContent: string; stopped: boolean; result: DiagnosisResponse | null; error: string | null; onStop: () => void; onRetry: () => void; onNewScan: () => void; }

export function DiagnosisConversation({ preview, filename, loading, phaseMessage, streamedContent, stopped, result, error, onStop, onRetry, onNewScan }: DiagnosisConversationProps) {
  const hasStream = streamedContent.length > 0;
  return <div className="space-y-10 py-4"><UserMessage preview={preview} filename={filename}/>{loading && !hasStream && <LoadingState message={phaseMessage}/>} {hasStream && <StreamedResponse content={streamedContent} streaming={loading} stopped={stopped} onStop={onStop} onRetry={onRetry}/>} {error && <ErrorState message={error} onRetry={onRetry} onNewScan={onNewScan}/>} {result && !hasStream && !loading && !error && <DiagnosisResult result={result}/>}</div>;
}
