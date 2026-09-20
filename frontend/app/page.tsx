'use client';
import React from 'react';
import Link from 'next/link';

import type { ScanType, StandardReport } from '../lib/types';
import { Navbar } from '../components/ui/Navbar';
import { HeroSection } from '../components/ui/HeroSection';
import { StandardsReportPanel } from '../components/panels/StandardsReportPanel';
import { useScanState } from '../hooks/useScanState';
import { unwrapReportData } from '../lib/utils';

export default function Home() {
  const scan = useScanState();

  const handleUrlChange = (newUrl: string) => {
    scan.setUrl(newUrl);
  };

  return (
    <>
      <div className="crt-overlay" aria-hidden="true" />
      <div className="bg-orbs" aria-hidden="true" />

      <div className="page-wrapper">
        <Navbar />
        <HeroSection />

        {/* Scanner Card */}
        <main id="main-content">
          <section className="scanner-card fade-in-delay-2" aria-label="URL Scanner">
            <label htmlFor="url-input" className="scanner-label">
              // ระบุ URL เป้าหมาย (Target URL)
            </label>

            <div className="scan-type-selector" id="scan-type-selector" role="group" aria-label="Scan type">
              {(['standards', 'wcag', 'cwv', 'ncsa', 'owasp'] as ScanType[]).map((type) => {
                const standardsReport = unwrapReportData(scan.resultsByType['standards']);
                const hasResult = !!(
                  scan.resultsByType[type] ||
                  (standardsReport && (
                    type === 'standards' ||
                    (standardsReport.standards ?? []).some((s: StandardReport) => s.id === type)
                  ))
                );
                return (
                  <button
                    key={type}
                    id={`scan-type-${type}`}
                    className={`scan-type-btn ${scan.scanType === type ? 'active' : ''}`}
                    onClick={() => scan.handleSelectScanType(type)}
                    disabled={scan.loading}
                    aria-pressed={scan.scanType === type}
                  >
                    {type === 'standards'    && '📋 ทั้งหมด (71 ข้อ)'}
                    {type === 'wcag'          && '♿ WCAG (37 ข้อ)'}
                    {type === 'cwv'           && '📊 Web Vitals & SEO (9 ข้อ)'}
                    {type === 'ncsa'          && '🛡️ สกมช. (11 ข้อ)'}
                    {type === 'owasp'         && '🔒 OWASP Headers (14 ข้อ)'}
                    {hasResult && <span className="scan-tab-badge" title="มีผลสแกนแล้ว">✓</span>}
                  </button>
                );
              })}
            </div>

            <div className="input-group">
              <input
                id="url-input"
                type="url"
                className="url-input"
                value={scan.url}
                onChange={(e) => handleUrlChange(e.target.value)}
                onKeyDown={scan.handleKeyDown}
                placeholder="https://target.example.com"
                aria-label="URL ที่ต้องการสแกน"
                autoComplete="url"
                spellCheck={false}
              />
              {scan.url && !scan.loading && (
                <button
                  type="button"
                  className="url-clear-btn"
                  onClick={scan.handleReset}
                  aria-label="ล้างข้อมูล URL และผลการสแกน"
                  title="ล้างข้อมูลและเริ่มใหม่"
                >
                  ✕
                </button>
              )}
              <button
                id="scan-button"
                className="scan-btn"
                onClick={scan.handleScan}
                disabled={scan.loading || !scan.url}
                aria-label={scan.loading ? 'กำลังสแกน' : 'เริ่มสแกน'}
              >
                {scan.loading && <span className="spinner" aria-hidden="true" />}
                {scan.loading ? 'กำลังสแกน...' : '► เริ่มสแกน'}
              </button>
            </div>

            <div className="scan-status" aria-live="polite" aria-atomic="true">
              <span className={`status-dot ${scan.getStatusClass()}`} aria-hidden="true" />
              <span>{scan.getStatusText()}</span>
            </div>

            {scan.result?.error && (
              <div className="error-banner" role="alert" id="error-message">
                <span className="error-icon" aria-hidden="true">⚠</span>
                <span>{scan.result.error}</span>
              </div>
            )}

            {/* Results */}
            {scan.showResult && (
              <div className="results-wrapper" id="scan-results">
                <div className="results-header">
                  <span className="results-title">// ผลการตรวจสอบ (OUTPUT)</span>
                  <button
                    onClick={scan.handleReset}
                    className="dash-action-btn results-clear-btn"
                    title="ล้างผลการสแกนและเริ่มใหม่"
                  >
                    ✕ ล้างผลสแกน
                  </button>
                </div>

                <div className="results-panels">
                  <StandardsReportPanel
                    data={scan.result}
                    expandedMap={scan.expandedMap}
                    onToggleStd={(id, isExp) => scan.setExpandedMap((prev) => ({ ...prev, [id]: isExp }))}
                  />
                </div>

                {/* Dashboard Action */}
                <div className="ai-trigger-row">
                  <Link
                    href="/dashboard"
                    id="view-dashboard-button"
                    className="scan-btn dashboard-link-btn"
                  >
                    📊 ดูแดชบอร์ดสรุปผล
                  </Link>
                </div>
              </div>
            )}
          </section>
        </main>

        {/* Footer */}
        <footer className="footer" id="site-footer">
          <p>
            © 2026 WebScan &mdash; Automated Web Standards &amp; Vulnerability Assessment ·{' '}
            <a href="https://github.com" target="_blank" rel="noopener noreferrer">
              GitHub
            </a>
          </p>
        </footer>
      </div>
    </>
  );
}