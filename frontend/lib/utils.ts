/**
 * Shared utility functions for scan result processing.
 */
import type { StandardReport, CheckItem, ScanResultsMap, ScanApiResponse, StandardsReportData } from './types';


/**
 * Normalize a URL for comparison: trim, strip trailing slashes, lowercase.
 */
export function normalizeUrl(url: string): string {
  return url.trim().replace(/\/+$/, '').toLowerCase();
}


/**
 * Extract all checks with a given status from standards data.
 */
export function extractChecks(standards: StandardReport[], status: string): CheckItem[] {
  const items: CheckItem[] = [];
  for (const std of standards) {
    for (const cat of std.categories ?? []) {
      for (const check of cat.checks ?? []) {
        if (check.status === status) {
          items.push({ ...check, standardId: std.id, standardName: std.name });
        }
      }
    }
  }
  return items;
}


/**
 * Unwrap a ScanApiResponse to get the inner StandardsReportData.
 */
export function unwrapReportData(raw: ScanApiResponse | null | undefined): StandardsReportData | null {
  if (!raw) return null;
  // The API returns { success, scan_id, data: StandardsReportData }
  // But sometimes the data is the raw object itself (from localStorage)
  const inner = (raw as Record<string, unknown>).data ?? raw;
  if (inner && typeof inner === 'object' && 'standards' in inner) {
    return inner as StandardsReportData;
  }
  return null;
}


/**
 * Combine individual scan results from a results-by-type map into a
 * unified StandardsReportData for the dashboard.
 */
export function combineScanResults(
  resultsByType: ScanResultsMap,
  currentDashboardData: ScanApiResponse | null
): StandardsReportData | null {
  if (!resultsByType || Object.keys(resultsByType).length === 0) {
    return unwrapReportData(currentDashboardData);
  }

  // Determine active target URL
  const primaryUrl =
    unwrapReportData(currentDashboardData)?.url ||
    unwrapReportData(resultsByType['standards'] ?? null)?.url ||
    '';

  const normPrimary = normalizeUrl(primaryUrl);

  // If full 'standards' scan exists and matches primary URL, use that directly
  if (resultsByType['standards']) {
    const stdData = unwrapReportData(resultsByType['standards'] ?? null);
    const stdUrl = normalizeUrl(stdData?.url || '');
    if (!normPrimary || !stdUrl || stdUrl === normPrimary) {
      return stdData;
    }
  }

  // Otherwise, combine only individual scans that belong to the same target URL
  const stdKeys = ['wcag', 'cwv', 'ncsa', 'owasp'] as const;
  const standardsList: StandardReport[] = [];
  const seenStdIds = new Set<string>();
  let totalP = 0;
  let totalF = 0;
  let totalW = 0;
  let totalItems = 0;
  let allTechs: StandardsReportData['wappalyzer_technologies'] = [];
  let url = '';
  let timestamp = '';

  for (const k of stdKeys) {
    const raw = resultsByType[k];
    if (!raw) continue;
    const rData = unwrapReportData(raw);
    if (!rData) continue;
    const itemUrl = normalizeUrl(rData.url || '');
    if (normPrimary && itemUrl && itemUrl !== normPrimary) continue;
    if (rData.url) url = rData.url;
    if (rData.timestamp) timestamp = rData.timestamp;
    if (rData.wappalyzer_technologies?.length) {
      allTechs = [...(allTechs || []), ...rData.wappalyzer_technologies];
    }
    for (const std of rData.standards ?? []) {
      if (!seenStdIds.has(std.id)) {
        seenStdIds.add(std.id);
        standardsList.push(std);
        totalP += std.passed ?? 0;
        totalF += std.failed ?? 0;
        totalW += std.warning ?? 0;
        totalItems += std.total ?? 0;
      }
    }
  }

  if (standardsList.length > 0) {
    return {
      url: url || primaryUrl || unwrapReportData(currentDashboardData)?.url || '',
      timestamp: timestamp || unwrapReportData(currentDashboardData)?.timestamp || '',
      summary: {
        total: totalItems,
        passed: totalP,
        failed: totalF,
        warning: totalW,
      },
      standards: standardsList,
      wappalyzer_technologies: allTechs,
    };
  }

  return unwrapReportData(currentDashboardData);
}
