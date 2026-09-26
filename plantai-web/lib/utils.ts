const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];
const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatConfidence(value: number): string {
  return `${Math.round(value * 100)}% confidence`;
}

export function validateImageFile(file: File): string | null {
  if (!ALLOWED_TYPES.includes(file.type)) return "Choose a JPG, JPEG, PNG, or WEBP image.";
  if (file.size > MAX_UPLOAD_BYTES) return "Choose an image smaller than 10 MB.";
  return null;
}

export function fileToDataUrl(file: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(new Error("Could not read the selected image."));
    reader.readAsDataURL(file);
  });
}

export async function optimizeImage(file: File): Promise<File> {
  if (file.type === "image/webp" || file.size < 2 * 1024 * 1024) return file;
  const url = URL.createObjectURL(file);
  try {
    const image = await new Promise<HTMLImageElement>((resolve, reject) => {
      const element = new Image();
      element.onload = () => resolve(element);
      element.onerror = () => reject(new Error("Could not decode this image."));
      element.src = url;
    });
    const maxDimension = 2400;
    const scale = Math.min(1, maxDimension / Math.max(image.naturalWidth, image.naturalHeight));
    if (scale === 1 && file.type === "image/jpeg") return file;
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(image.naturalWidth * scale);
    canvas.height = Math.round(image.naturalHeight * scale);
    const context = canvas.getContext("2d");
    if (!context) return file;
    context.drawImage(image, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.9));
    if (!blob || blob.size >= file.size) return file;
    return new File([blob], file.name.replace(/\.[^.]+$/, ".jpg"), { type: "image/jpeg" });
  } finally {
    URL.revokeObjectURL(url);
  }
}

export function historyDate(iso: string): string {
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }).format(new Date(iso));
}
