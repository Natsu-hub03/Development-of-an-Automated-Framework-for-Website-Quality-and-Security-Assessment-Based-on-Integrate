/**
 * Core type definitions for WebScan frontend.
 */

export type ScanType = 'standards' | 'wcag' | 'cwv' | 'ncsa' | 'owasp';

export type CheckStatus = 'pass' | 'fail' | 'warning' | 'info';

export type ScanStatus = 'idle' | 'scanning' | 'done' | 'error';

export interface EvidenceNode {
  target?: string[];
  html?: string;
  failureSummary?: string;
  passed_summary?: string;
  summary?: string;
}

export interface CheckItem {
  id: string;
  name: string;
  name_th: string;
  why_th?: string;
  remediation_th?: string;
  standard: string;
  category: string;
  status: CheckStatus;
  detail: string;
  source_tool: string;
  evidence?: EvidenceNode[];
  evidence_type?: string;
  standardId?: string;
  standardName?: string;
}

export interface CategoryGroup {
  name: string;
  checks: CheckItem[];
}

export interface StandardReport {
  id: string;
  name: string;
  name_full: string;
  owner: string;
  icon: string;
  total: number;
  passed: number;
  failed: number;
  warning: number;
  categories: CategoryGroup[];
}

export interface Technology {
  name: string;
  version?: string | null;
  icon?: string;
  categories?: { name: string }[];
}

export interface StandardsScanSummary {
  total: number;
  passed: number;
  failed: number;
  warning: number;
}

export interface StandardsReportData {
  url: string;
  timestamp: string;
  summary: StandardsScanSummary;
  standards: StandardReport[];
  wappalyzer_technologies?: Technology[];
}

export interface ScanApiResponse {
  success?: boolean;
  scan_id?: number;
  data?: StandardsReportData;
  error?: string;
  url?: string;
  model?: string;
  analysis?: string;
}

export type ScanResultsMap = Partial<Record<ScanType, ScanApiResponse>>;
