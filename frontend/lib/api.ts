/**
 * API client functions for communicating with backend services.
 */
import { API_BASE_URL } from './constants';
import type { ScanType, ScanApiResponse } from './types';

export function getScanEndpoint(type: ScanType): string {
  if (type === 'standards') return '/scan/standards';
  return `/scan/standard/${type}`;
}

const DEFAULT_SCAN_TIMEOUT = 180_000; // 3 minutes for comprehensive multi-tool scans
const DEFAULT_AI_TIMEOUT = 180_000;   // 3 minutes for Ollama analysis

export async function executeScan(
  type: ScanType,
  targetUrl: string,
  timeoutMs = DEFAULT_SCAN_TIMEOUT
): Promise<ScanApiResponse> {
  const endpoint = getScanEndpoint(type);
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: targetUrl }),
      signal: controller.signal,
    });

    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      return {
        error: errBody.detail || `Server error (${res.status}): ${res.statusText}`,
      };
    }

    return await res.json();
  } catch (err: unknown) {
    if (err instanceof Error && err.name === 'AbortError') {
      return { error: 'การสแกนหมดเวลา (Request timed out)' };
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function executeAiAnalysis(
  url: string,
  scanData: unknown,
  scanType: string,
  timeoutMs = DEFAULT_AI_TIMEOUT
): Promise<ScanApiResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(`${API_BASE_URL}/analyze/ai`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, scan_data: scanData, scan_type: scanType }),
      signal: controller.signal,
    });

    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      return {
        error: errBody.detail || `AI service error (${res.status}): ${res.statusText}`,
      };
    }

    return await res.json();
  } catch (err: unknown) {
    if (err instanceof Error && err.name === 'AbortError') {
      return { error: 'การวิเคราะห์ AI หมดเวลา (Request timed out)' };
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}


export interface AiBatchItem {
  check_id: string;
  check_name: string;
  check_name_th?: string;
  status: string;
  detail: string;
  evidence?: unknown;
}

export interface AiBatchResult {
  ai_risk: string;
  ai_fix: string;
}

export interface AiBatchResponse {
  success?: boolean;
  results?: Record<string, AiBatchResult>;
  error?: string;
}

const DEFAULT_AI_BATCH_TIMEOUT = 300_000; // 5 minutes for batch

export async function executeAiBatchFix(
  items: AiBatchItem[],
  timeoutMs = DEFAULT_AI_BATCH_TIMEOUT
): Promise<AiBatchResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(`${API_BASE_URL}/analyze/ai-batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ items }),
      signal: controller.signal,
    });

    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      return {
        error: errBody.detail || `AI batch error (${res.status}): ${res.statusText}`,
      };
    }

    return await res.json();
  } catch (err: unknown) {
    if (err instanceof Error && err.name === 'AbortError') {
      return { error: 'AI batch analysis timed out' };
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}
