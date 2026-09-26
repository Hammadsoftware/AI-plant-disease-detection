import type { HistoryItem } from "@/lib/types";

const HISTORY_KEY = "plantai.scan-history.v1";
const MAX_ITEMS = 8;

export function loadHistory(): HistoryItem[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(HISTORY_KEY);
    if (!raw) return [];
    const parsed: HistoryItem[] = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function saveHistory(items: HistoryItem[]): HistoryItem[] {
  const next = items.slice(0, MAX_ITEMS);
  try {
    window.localStorage.setItem(HISTORY_KEY, JSON.stringify(next));
    return next;
  } catch {
    const compact = next.slice(0, 3);
    try {
      window.localStorage.setItem(HISTORY_KEY, JSON.stringify(compact));
    } catch {
      return items;
    }
    return compact;
  }
}
