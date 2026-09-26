import type {
  ApiErrorShape,
  DiagnosisResponse,
  HealthResponse,
  StreamCallbacks,
  StreamPhase,
  StreamedDiagnosis,
} from "@/lib/types";

const API_ORIGIN = (
  process.env.NEXT_PUBLIC_API_URL ?? "https://plant-disease-api-1-0-1.onrender.com"
).replace(/\/$/, "");
const API_URL = `${API_ORIGIN}/api/v1`;

export class PlantApiError extends Error implements ApiErrorShape {
  status: number | null;

  constructor(message: string, status: number | null = null) {
    super(message);
    this.name = "PlantApiError";
    this.status = status;
  }
}

function friendlyError(status: number, detail?: string): string {
  if (status === 400 || status === 413 || status === 422) {
    return detail || "PlantAI couldn’t analyze this image. Please try another clear leaf photo.";
  }
  if (status === 404) {
    return "The live diagnosis stream is not available on the deployed AI service.";
  }
  if (status === 503) return "PlantAI is temporarily unavailable. Please try again in a moment.";
  if (status >= 500) return "The analysis service encountered a problem. Please try again shortly.";
  return detail || "We couldn’t complete this request. Please try again.";
}

async function responseDetail(response: Response): Promise<string | undefined> {
  try {
    const body: {
      detail?: string | Array<{ msg?: string }>;
      error?: { message?: string };
    } = await response.json();
    if (typeof body.error?.message === "string") return body.error.message;
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) return body.detail.map((item) => item.msg).filter(Boolean).join(" ");
  } catch {
    return undefined;
  }
}

export async function checkHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch(`${API_URL}/health`, {
    method: "GET",
    cache: "no-store",
    signal,
  });
  if (!response.ok) throw new PlantApiError("Health check failed.", response.status);
  return response.json();
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isDiagnosisResponse(value: unknown): value is DiagnosisResponse {
  return isRecord(value) && value.success === true && isRecord(value.diagnosis)
    && typeof value.diagnosis.disease === "string";
}

function streamPhase(value: unknown): StreamPhase | null {
  if (value === "analyzing" || value === "researching" || value === "generating") return value;
  return null;
}

interface ParsedSseEvent {
  eventName: string;
  data: string;
}

function parseSseBlock(block: string): ParsedSseEvent | null {
  let eventName = "message";
  const data: string[] = [];
  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) eventName = line.slice(6).trim();
    if (line.startsWith("data:")) data.push(line.slice(5).replace(/^ /, ""));
  }
  return data.length ? { eventName, data: data.join("\n") } : null;
}

function readEventPayload(event: ParsedSseEvent): Record<string, unknown> {
  try {
    const parsed: unknown = JSON.parse(event.data);
    return isRecord(parsed) ? parsed : { type: event.eventName, content: String(parsed) };
  } catch {
    return { type: event.eventName, content: event.data };
  }
}

function eventType(event: ParsedSseEvent, payload: Record<string, unknown>): string {
  return typeof payload.type === "string" ? payload.type : event.eventName;
}

export async function diagnoseLeafStream(
  image: File,
  callbacks: StreamCallbacks,
  signal: AbortSignal,
): Promise<StreamedDiagnosis> {
  const formData = new FormData();
  formData.append("image", image);
  formData.append("include_web_research", "true");
  formData.append("include_pesticides", "true");
  formData.append("include_explanation", "true");

  try {
    const response = await fetch(`${API_URL}/diagnose/stream`, {
      method: "POST",
      body: formData,
      signal,
      headers: { Accept: "text/event-stream" },
    });
    if (!response.ok) {
      const detail = await responseDetail(response);
      throw new PlantApiError(friendlyError(response.status, detail), response.status);
    }
    if (!response.body) throw new PlantApiError("The diagnosis stream is unavailable.", response.status);

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let content = "";
    let result: DiagnosisResponse | null = null;
    let completed = false;

    const consume = (rawBlock: string) => {
      const event = parseSseBlock(rawBlock);
      if (!event) return;
      const payload = readEventPayload(event);
      const type = eventType(event, payload);

      if (type === "phase" || type === "status") {
        const phase = streamPhase(payload.phase);
        const message = typeof payload.message === "string" ? payload.message : "";
        if (phase && message) callbacks.onPhase(phase, message);
        return;
      }
      if (type === "token" || type === "chunk" || type === "delta") {
        const token = typeof payload.content === "string"
          ? payload.content
          : typeof payload.token === "string"
            ? payload.token
            : typeof payload.delta === "string" ? payload.delta : "";
        if (token) {
          content += token;
          callbacks.onToken(token);
        }
        return;
      }
      if (type === "metadata" || type === "result" || type === "diagnosis") {
        const candidate = payload.result ?? payload.data ?? payload.diagnosis_response ?? payload;
        if (isDiagnosisResponse(candidate)) {
          result = candidate;
          callbacks.onMetadata(candidate);
        }
        return;
      }
      if (type === "error") {
        const message = typeof payload.message === "string"
          ? payload.message
          : "Something went wrong while generating the diagnosis.";
        throw new PlantApiError(message);
      }
      if (type === "done" || type === "complete") {
        const candidate = payload.result ?? payload.data;
        if (isDiagnosisResponse(candidate)) {
          result = candidate;
          callbacks.onMetadata(candidate);
        }
        completed = true;
      }
    };

    while (true) {
      const { done, value } = await reader.read();
      buffer += decoder.decode(value, { stream: !done }).replace(/\r\n/g, "\n");
      let boundary = buffer.indexOf("\n\n");
      while (boundary !== -1) {
        consume(buffer.slice(0, boundary));
        buffer = buffer.slice(boundary + 2);
        boundary = buffer.indexOf("\n\n");
      }
      if (done) break;
    }
    if (buffer.trim()) consume(buffer);
    if (!completed) throw new PlantApiError("The diagnosis stream ended unexpectedly.");
    return { content, result };
  } catch (error) {
    if (error instanceof PlantApiError) throw error;
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new PlantApiError("PlantAI couldn’t reach the diagnosis service. Check your connection and try again.");
  }
}

export { API_URL };
