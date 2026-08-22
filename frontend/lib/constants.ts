/**
 * Configuration constants for UI status indicators, grades, and risk levels.
 */
import { CheckStatus } from './types';

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const RISK_CONFIG: Record<string, { label: string; cls: string }> = {
  High:          { label: 'HIGH', cls: 'risk-high' },
  Medium:        { label: 'MED',  cls: 'risk-medium' },
  Low:           { label: 'LOW',  cls: 'risk-low' },
  Informational: { label: 'INFO', cls: 'risk-info' },
};

export const IMPACT_CONFIG: Record<string, { label: string; cls: string }> = {
  critical: { label: 'CRITICAL', cls: 'impact-critical' },
  serious:  { label: 'SERIOUS',  cls: 'impact-serious' },
  moderate: { label: 'MODERATE', cls: 'impact-moderate' },
  minor:    { label: 'MINOR',    cls: 'impact-minor' },
};

export const STATUS_CONFIG: Record<CheckStatus, { icon: string; label: string; cls: string }> = {
  pass:    { icon: '✅', label: 'ผ่าน',    cls: 'status-pass' },
  fail:    { icon: '❌', label: 'ไม่ผ่าน', cls: 'status-fail' },
  warning: { icon: '⚠️', label: 'เตือน',   cls: 'status-warning' },
  info:    { icon: 'ℹ️', label: 'ข้อมูล',  cls: 'status-info' },
};

export const STANDARD_ICONS: Record<string, string> = {
  wcag: '♿',
  cwv: '📊',
  ncsa: '🛡️',
  owasp: '🔒',
};

export function scoreColorClass(score: number | null): string {
  if (score === null) return 'score-null';
  if (score >= 90) return 'score-good';
  if (score >= 50) return 'score-avg';
  return 'score-poor';
}

export function getGrade(pct: number): { label: string; cls: string } {
  if (pct >= 90) return { label: 'Excellent', cls: 'grade-excellent' };
  if (pct >= 70) return { label: 'Good', cls: 'grade-good' };
  if (pct >= 50) return { label: 'Fair', cls: 'grade-fair' };
  return { label: 'Needs Work', cls: 'grade-poor' };
}
