/**
 * API client functions for communicating with backend services.
 */
import { API_BASE_URL } from './constants';
import { ScanType, ScanApiResponse } from './types';

export function getScanEndpoint(type: ScanType): string {
  if (type === 'standards') return '/scan/standards';
  return `/scan/standard/${type}`;
}

export async function executeScan(type: ScanType, targetUrl: string): Promise<ScanApiResponse> {
  const endpoint = getScanEndpoint(type);
  const res = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url: targetUrl }),
  });
  return res.json();
}

export async function executeAiAnalysis(
  url: string,
  scanData: any,
  scanType: string
): Promise<ScanApiResponse> {
  const res = await fetch(`${API_BASE_URL}/analyze/ai`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, scan_data: scanData, scan_type: scanType }),
  });
  return res.json();
}
