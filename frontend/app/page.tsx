'use client';
import React, { useState, useEffect } from 'react';
import Link from 'next/link';

import { ScanType, ScanResultsMap, ScanApiResponse } from '../lib/types';
import { executeScan, executeAiAnalysis } from '../lib/api';
import { Navbar } from '../components/ui/Navbar';
import { HeroSection } from '../components/ui/HeroSection';
import { FeatureCards } from '../components/ui/FeatureCards';
import { StandardsReportPanel } from '../components/panels/StandardsReportPanel';
import { AiReportPanel } from '../components/panels/AiReportPanel';

export default function Home() {
  const [url, setUrl]                     = useState('');
  const [lastScannedUrl, setLastScannedUrl] = useState<string>('');
  const [result, setResult]               = useState<any>(null);
  const [loading, setLoading]             = useState(false);
  const [scanStatus, setScanStatus]       = useState<'idle' | 'scanning' | 'done' | 'error'>('idle');
  const [scanType, setScanType]           = useState<ScanType>('standards');
  const [resultsByType, setResultsByType] = useState<ScanResultsMap>({});
  const [expandedMap, setExpandedMap]     = useState<Record<string, boolean>>({});
  const [aiResult, setAiResult]           = useState<string | null>(null);
  const [aiModel, setAiModel]             = useState<string>('qwen2.5:3b');
  const [aiLoading, setAiLoading]         = useState(false);
  const [aiError, setAiError]             = useState<string | null>(null);

  // Restore state from localStorage if available
  useEffect(() => {
    try {
      const savedMap = localStorage.getItem('webscan_results_by_type');
      let map: ScanResultsMap = {};
      if (savedMap) {
        map = JSON.parse(savedMap);
        setResultsByType(map);
      }

      const saved = localStorage.getItem('webscan_state');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.url) {
          setUrl(parsed.url);
          setLastScannedUrl(parsed.lastScannedUrl || parsed.url);
        }
        const activeType = (parsed.scanType as ScanType) || 'standards';
        setScanType(activeType);

        if (parsed.resultsByType) {
          map = { ...map, ...parsed.resultsByType };
          setResultsByType(map);
        }

        const res = map[activeType] || parsed.result;
        if (res) {
          setResult(res);
          setScanStatus('done');
        }
        if (parsed.aiResult) setAiResult(parsed.aiResult);
        if (parsed.aiModel) setAiModel(parsed.aiModel);
      } else {
        const legacyData = localStorage.getItem('webscan_dashboard_data');
        if (legacyData) {
          const parsed = JSON.parse(legacyData);
          setResult(parsed);
          setScanStatus('done');
          const targetUrl = parsed.url || parsed.data?.url || '';
          if (targetUrl) {
            setUrl(targetUrl);
            setLastScannedUrl(targetUrl);
          }
        }
      }
    } catch {
      // ignore parse errors
    }
  }, []);

  const handleSelectScanType = (type: ScanType) => {
    setScanType(type);
    let existing = resultsByType[type];

    // If sub-standard not yet explicitly stored, extract from all-standards result
    if (!existing && resultsByType['standards']) {
      const allReport = resultsByType['standards']?.data ?? resultsByType['standards'];
      const std = (allReport?.standards ?? []).find((s: any) => s.id === type);
      if (std) {
        existing = {
          success: true,
          url: allReport.url || url,
          timestamp: allReport.timestamp,
          standard: std,
          summary: {
            total: std.total,
            passed: std.passed,
            failed: std.failed,
            warning: std.warning,
          },
          wappalyzer_technologies: allReport.wappalyzer_technologies,
          axe_results: allReport.axe_results,
          lighthouse_results: allReport.lighthouse_results,
          headers_results: allReport.headers_results,
          zap_results: allReport.zap_results,
        };
      }
    }

    if (existing) {
      setResult(existing);
      setScanStatus('done');
    } else {
      setResult(null);
      setScanStatus('idle');
    }
    setAiResult(null);
    setAiError(null);
  };

  const handleScan = async () => {
    const trimmedUrl = url.trim();
    if (!trimmedUrl) return;

    const normNew = trimmedUrl.replace(/\/+$/, '').toLowerCase();
    const normOld = (lastScannedUrl || '').trim().replace(/\/+$/, '').toLowerCase();
    const isNewUrl = !normOld || normNew !== normOld;

    setLoading(true);
    setResult(null);
    setAiResult(null);
    setAiError(null);
    setScanStatus('scanning');

    // If new URL, flush all previous results completely from memory & localStorage
    let baseMap: ScanResultsMap = {};
    if (isNewUrl) {
      setResultsByType({});
      setExpandedMap({});
      setLastScannedUrl(trimmedUrl);
      try {
        localStorage.removeItem('webscan_results_by_type');
        localStorage.removeItem('webscan_dashboard_data');
        localStorage.removeItem('webscan_state');
      } catch {}
    } else {
      baseMap = { ...resultsByType };
    }

    try {
      const data = await executeScan(scanType, trimmedUrl);
      setResult(data);
      setScanStatus('done');
      setLastScannedUrl(trimmedUrl);

      const updatedMap: ScanResultsMap = {
        ...baseMap,
        [scanType]: data,
      };

      // If all standards were scanned, automatically populate all individual sub-standards
      if (scanType === 'standards' && data) {
        const reportData = data?.data ?? data;
        const stdList: any[] = reportData?.standards ?? [];
        for (const std of stdList) {
          if (std?.id) {
            const stdId = std.id as ScanType;
            updatedMap[stdId] = {
              success: true,
              url: reportData.url || trimmedUrl,
              timestamp: reportData.timestamp,
              standard: std,
              summary: {
                total: std.total,
                passed: std.passed,
                failed: std.failed,
                warning: std.warning,
              },
              wappalyzer_technologies: reportData.wappalyzer_technologies,
              axe_results: reportData.axe_results,
              lighthouse_results: reportData.lighthouse_results,
              headers_results: reportData.headers_results,
              zap_results: reportData.zap_results,
            };
          }
        }
      }

      setResultsByType(updatedMap);

      // Save to localStorage strictly for the current URL
      try {
        localStorage.setItem('webscan_results_by_type', JSON.stringify(updatedMap));
        localStorage.setItem('webscan_dashboard_data', JSON.stringify(data));
        localStorage.setItem(
          'webscan_state',
          JSON.stringify({
            url: trimmedUrl,
            lastScannedUrl: trimmedUrl,
            scanType,
            resultsByType: updatedMap,
            result: data,
            aiResult: null,
            aiModel: 'qwen2.5:3b',
          })
        );
      } catch { /* ignore quota errors */ }
    } catch (err) {
      console.error(err);
      setResult({ error: 'ไม่สามารถเชื่อมต่อกับ Backend ได้ กรุณาตรวจสอบว่า Server กำลังทำงานอยู่' });
      setScanStatus('error');
    }
    setLoading(false);
  };

  const handleAiAnalyze = async () => {
    if (!result || !url) return;
    setAiLoading(true);
    setAiError(null);
    setAiResult(null);
    try {
      const data: ScanApiResponse = await executeAiAnalysis(url, result, scanType);
      if (!data || data.error || !data.success) {
        setAiError(data.error || 'AI analysis failed');
      } else {
        const text = data.analysis || '';
        const model = data.model || 'qwen2.5:3b';
        setAiResult(text);
        setAiModel(model);
        try {
          localStorage.setItem(
            'webscan_state',
            JSON.stringify({
              url: url.trim(),
              lastScannedUrl: lastScannedUrl || url.trim(),
              scanType,
              resultsByType,
              result,
              aiResult: text,
              aiModel: model,
            })
          );
        } catch {}
      }
    } catch {
      setAiError('ไม่สามารถเชื่อมต่อกับ AI service ได้');
    }
    setAiLoading(false);
  };

  const handleReset = () => {
    setUrl('');
    setLastScannedUrl('');
    setResult(null);
    setAiResult(null);
    setAiError(null);
    setScanStatus('idle');
    setResultsByType({});
    setExpandedMap({});
    try {
      localStorage.removeItem('webscan_state');
      localStorage.removeItem('webscan_dashboard_data');
      localStorage.removeItem('webscan_results_by_type');
    } catch {}
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && url && !loading) handleScan();
  };

  const getStatusText = () => {
    switch (scanStatus) {
      case 'idle':     return '> READY';
      case 'scanning': return scanType === 'standards'
        ? '> SCANNING ALL STANDARDS (this may take a minute)...'
        : scanType === 'ncsa'
        ? '> SCANNING สกมช. (NCSA Guidelines)...'
        : '> SCANNING...';
      case 'done':     return '> SCAN COMPLETE';
      case 'error':    return '> ERROR';
    }
  };

  const getStatusClass = () => {
    switch (scanStatus) {
      case 'idle':     return '';
      case 'scanning': return 'scanning';
      case 'done':     return 'ready';
      case 'error':    return 'error';
    }
  };

  const showResult = result && !result.error;

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
              // Target URL
            </label>

            <div className="scan-type-selector" id="scan-type-selector" role="group" aria-label="Scan type">
              {(['standards', 'wcag', 'cwv', 'ncsa', 'owasp'] as ScanType[]).map((type) => {
                const hasResult = !!(
                  resultsByType[type] ||
                  (resultsByType['standards'] && (
                    type === 'standards' ||
                    ((resultsByType['standards']?.data ?? resultsByType['standards'])?.standards ?? []).some((s: any) => s.id === type)
                  ))
                );
                return (
                  <button
                    key={type}
                    id={`scan-type-${type}`}
                    className={`scan-type-btn ${scanType === type ? 'active' : ''}`}
                    onClick={() => handleSelectScanType(type)}
                    disabled={loading}
                    aria-pressed={scanType === type}
                  >
                    {type === 'standards'    && '📋 ทั้งหมด (68 ข้อ)'}
                    {type === 'wcag'          && '♿ WCAG (37 ข้อ)'}
                    {type === 'cwv'           && '📊 Web Vitals & SEO (9 ข้อ)'}
                    {type === 'ncsa'          && '🛡️ สกมช. (11 ข้อ)'}
                    {type === 'owasp'         && '🔒 OWASP Headers (11 ข้อ)'}
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
                value={url}
                onChange={(e) => {
                  const newUrl = e.target.value;
                  setUrl(newUrl);
                  const normNew = newUrl.trim().replace(/\/+$/, '').toLowerCase();
                  const normOld = (lastScannedUrl || '').trim().replace(/\/+$/, '').toLowerCase();
                  if (normOld && normNew !== normOld) {
                    setResult(null);
                    setAiResult(null);
                    setAiError(null);
                    setScanStatus('idle');
                  }
                }}
                onKeyDown={handleKeyDown}
                placeholder="https://target.example.com"
                aria-label="URL ที่ต้องการสแกน"
                autoComplete="url"
                spellCheck={false}
              />
              {url && !loading && (
                <button
                  type="button"
                  className="url-clear-btn"
                  onClick={handleReset}
                  aria-label="ล้างข้อมูล URL และผลการสแกน"
                  title="ล้างข้อมูลและเริ่มใหม่"
                >
                  ✕
                </button>
              )}
              <button
                id="scan-button"
                className="scan-btn"
                onClick={handleScan}
                disabled={loading || !url}
                aria-label={loading ? 'กำลังสแกน' : 'เริ่มสแกน'}
              >
                {loading && <span className="spinner" aria-hidden="true" />}
                {loading ? 'SCANNING...' : '► RUN SCAN'}
              </button>
            </div>

            <div className="scan-status" aria-live="polite" aria-atomic="true">
              <span className={`status-dot ${getStatusClass()}`} aria-hidden="true" />
              <span>{getStatusText()}</span>
            </div>

            {result?.error && (
              <div className="error-banner" role="alert" id="error-message">
                <span className="error-icon" aria-hidden="true">⚠</span>
                <span>{result.error}</span>
              </div>
            )}

            {/* Results */}
            {showResult && (
              <div className="results-wrapper" id="scan-results">
                <div className="results-header">
                  <span className="results-title">// OUTPUT</span>
                  <button
                    onClick={handleReset}
                    className="dash-action-btn"
                    style={{ fontSize: '10px', padding: '4px 10px', minHeight: 'auto' }}
                    title="ล้างผลการสแกนและเริ่มใหม่"
                  >
                    ✕ CLEAR / ล้างผล
                  </button>
                </div>

                <div className="results-panels">
                  <StandardsReportPanel
                    data={result}
                    expandedMap={expandedMap}
                    onToggleStd={(id, isExp) => setExpandedMap((prev) => ({ ...prev, [id]: isExp }))}
                  />
                </div>

                {/* Dashboard + AI buttons */}
                <div className="ai-trigger-row">
                  <Link
                    href="/dashboard"
                    id="view-dashboard-button"
                    className="scan-btn"
                    style={{ textDecoration: 'none', fontSize: '13px', padding: '11px 22px' }}
                  >
                    📊 VIEW DASHBOARD
                  </Link>
                  <button
                    id="ai-analyze-button"
                    className="ai-btn"
                    onClick={handleAiAnalyze}
                    disabled={aiLoading}
                    aria-label="วิเคราะห์ด้วย AI"
                  >
                    {aiLoading
                      ? <><span className="spinner spinner--dark" aria-hidden="true" /> ANALYZING...</>
                      : <>✦ AI SECURITY ANALYSIS</>
                    }
                  </button>
                  {aiResult && (
                    <span className="ai-model-badge">{aiModel} · Ollama</span>
                  )}
                </div>

                {aiError && (
                  <div className="error-banner" role="alert" id="ai-error-message">
                    <span className="error-icon" aria-hidden="true">⚠</span>
                    <span>{aiError}</span>
                  </div>
                )}

                {aiResult && (
                  <AiReportPanel url={url} analysis={aiResult} model={aiModel} />
                )}
              </div>
            )}
          </section>
        </main>

        <FeatureCards />

        {/* Footer */}
        <footer className="footer" id="site-footer">
          <p>
            © 2026 WebScan &mdash; AI-Assisted Web Standards &amp; Vulnerability Assessment ·{' '}
            <a href="https://github.com" target="_blank" rel="noopener noreferrer">
              GitHub
            </a>
          </p>
        </footer>
      </div>
    </>
  );
}