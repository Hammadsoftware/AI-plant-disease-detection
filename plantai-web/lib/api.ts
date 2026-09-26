import type {
  ApiErrorShape,
  DiagnosisResponse,
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
    return "The diagnosis endpoint is not available on the deployed AI service.";
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

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isDiagnosisResponse(value: unknown): value is DiagnosisResponse {
  return isRecord(value) && value.success === true && isRecord(value.diagnosis)
    && typeof value.diagnosis.disease === "string";
}

export async function diagnoseLeaf(
  image: File,
  signal: AbortSignal,
): Promise<DiagnosisResponse> {
  const formData = new FormData();
  formData.append("image", image);
  formData.append("include_web_research", "true");
  formData.append("include_pesticides", "true");
  formData.append("include_explanation", "true");

  try {
    const response = await fetch(`${API_URL}/diagnose`, {
      method: "POST",
      body: formData,
      signal,
      headers: { Accept: "application/json" },
    });
    if (!response.ok) {
      const detail = await responseDetail(response);
      throw new PlantApiError(friendlyError(response.status, detail), response.status);
    }
    const body: unknown = await response.json();
    if (!isDiagnosisResponse(body)) {
      throw new PlantApiError("The diagnosis service returned an invalid response.", response.status);
    }
    return body;
  } catch (error) {
    if (error instanceof PlantApiError) throw error;
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new PlantApiError("PlantAI couldn’t reach the diagnosis service. Check your connection and try again.");
  }
}

export { API_URL };
