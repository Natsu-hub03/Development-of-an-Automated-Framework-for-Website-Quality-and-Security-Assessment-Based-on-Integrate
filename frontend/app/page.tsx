'use client';
import { useState } from 'react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

type ScanType = 'standards' | 'wappalyzer' | 'zap' | 'axe' | 'lighthouse';

const RISK_CONFIG: Record<string, { label: string; cls: string }> = {
  High:          { label: 'HIGH', cls: 'risk-high' },
  Medium:        { label: 'MED',  cls: 'risk-medium' },
  Low:           { label: 'LOW',  cls: 'risk-low' },
  Informational: { label: 'INFO', cls: 'risk-info' },
};

const IMPACT_CONFIG: Record<string, { label: string; cls: string }> = {
  critical: { label: 'CRITICAL', cls: 'impact-critical' },
  serious:  { label: 'SERIOUS',  cls: 'impact-serious' },
  moderate: { label: 'MODERATE', cls: 'impact-moderate' },
  minor:    { label: 'MINOR',    cls: 'impact-minor' },
};

const STATUS_CONFIG: Record<string, { icon: string; label: string; cls: string }> = {
  pass:    { icon: '✅', label: 'ผ่าน',    cls: 'status-pass' },
  fail:    { icon: '❌', label: 'ไม่ผ่าน', cls: 'status-fail' },
  warning: { icon: '⚠️', label: 'เตือน',   cls: 'status-warning' },
};

const STANDARD_ICONS: Record<string, string> = {
  wcag: '♿',
  cwv: '📊',
  ncsa: '🛡️',
  owasp: '🔒',
};

// ── Score color helper ─────────────────────────────────────────────────────────
function scoreColorClass(score: number | null): string {
  if (score === null) return 'score-null';
  if (score >= 90) return 'score-good';
  if (score >= 50) return 'score-avg';
  return 'score-poor';
}

// ── Wappalyzer icon helper ────────────────────────────────────────────────────
function TechIcon({ tech }: { tech: any }) {
  const icon = tech.icon;
  const name = tech.name || '?';

  if (icon) {
    const iconUrl = `https://www.wappalyzer.com/images/icons/${icon}`;
    return (
      <img
        src={iconUrl}
        alt={name}
        className="wap-tech-icon"
        onError={(e) => {
          const target = e.target as HTMLImageElement;
          target.style.display = 'none';
          target.parentElement?.querySelector('.wap-tech-fallback')?.classList.remove('hidden');
        }}
      />
    );
  }
  return null;
}

// ── Standards Report Panel ────────────────────────────────────────────────────
function StandardsReportPanel({ data }: { data: any }) {
  const reportData = data?.data ?? data;
  const standards: any[] = reportData?.standards ?? [];
  const summary = reportData?.summary ?? {};
  const technologies: any[] = reportData?.wappalyzer_technologies ?? [];
  const [expandedStd, setExpandedStd] = useState<string | null>(null);
  const [techPage, setTechPage] = useState(0);
  const TECH_PER_PAGE = 10;

  const toggleStd = (id: string) => {
    setExpandedStd(expandedStd === id ? null : id);
  };

  const totalPages = Math.ceil(technologies.length / TECH_PER_PAGE);
  const pagedTechs = technologies.slice(
    techPage * TECH_PER_PAGE,
    (techPage + 1) * TECH_PER_PAGE
  );

  return (
    <div className="standards-report">
      {/* Summary Bar */}
      <div className="standards-summary">
        <div className="standards-summary-title">
          // STANDARDS COMPLIANCE REPORT
        </div>
        <div className="standards-summary-stats">
          <div className="stat-card stat-total">
            <div className="stat-value">{summary.total ?? 68}</div>
            <div className="stat-label">ทั้งหมด</div>
          </div>
          <div className="stat-card stat-pass">
            <div className="stat-value">{summary.passed ?? 0}</div>
            <div className="stat-label">ผ่าน</div>
          </div>
          <div className="stat-card stat-fail">
            <div className="stat-value">{summary.failed ?? 0}</div>
            <div className="stat-label">ไม่ผ่าน</div>
          </div>
          <div className="stat-card stat-warn">
            <div className="stat-value">{summary.warning ?? 0}</div>
            <div className="stat-label">เตือน</div>
          </div>
        </div>
      </div>

      {/* Per-Standard Cards */}
      <div className="standards-cards">
        {standards.map((std: any) => {
          const isExpanded = expandedStd === std.id;
          const passRate = std.total > 0
            ? Math.round((std.passed / std.total) * 100)
            : 0;

          return (
            <div key={std.id} className={`standard-card ${isExpanded ? 'expanded' : ''}`}>
              <button
                className="standard-card-header"
                onClick={() => toggleStd(std.id)}
                aria-expanded={isExpanded}
              >
                <div className="standard-card-left">
                  <span className="standard-icon">{STANDARD_ICONS[std.id] ?? '📋'}</span>
                  <div className="standard-card-info">
                    <div className="standard-card-name">{std.name}</div>
                    <div className="standard-card-owner">{std.owner}</div>
                  </div>
                </div>
                <div className="standard-card-right">
                  <div className="standard-card-counts">
                    <span className="count-pass">{std.passed}✅</span>
                    <span className="count-fail">{std.failed}❌</span>
                    <span className="count-warn">{std.warning}⚠️</span>
                  </div>
                  <div className="standard-progress-bar">
                    <div
                      className="standard-progress-fill"
                      style={{ width: `${passRate}%` }}
                    />
                  </div>
                  <span className="standard-progress-text">{passRate}%</span>
                  <span className={`standard-expand-icon ${isExpanded ? 'rotated' : ''}`}>▼</span>
                </div>
              </button>

              {isExpanded && (
                <div className="standard-card-body">
                  {(std.categories ?? []).map((cat: any) => (
                    <div key={cat.name} className="checklist-category">
                      <div className="checklist-category-name">{cat.name}</div>
                      <div className="checklist-items">
                        {(cat.checks ?? []).map((check: any) => {
                          const cfg = STATUS_CONFIG[check.status] ?? STATUS_CONFIG.warning;
                          return (
                            <div key={check.id} className={`checklist-item ${cfg.cls}`}>
                              <span className="checklist-status-icon">{cfg.icon}</span>
                              <div className="checklist-item-info">
                                <div className="checklist-item-name">
                                  {check.name}
                                  <span className="checklist-item-id">{check.id}</span>
                                </div>
                                <div className="checklist-item-name-th">{check.name_th}</div>
                                <div className="checklist-item-detail">{check.detail}</div>
                              </div>
                              <span className={`checklist-status-badge ${cfg.cls}`}>
                                {cfg.label}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Wappalyzer Technologies Table */}
      {technologies.length > 0 && (
        <div className="wap-table-section">
          <div className="wap-table-header-bar">
            <span className="wap-table-icon">🛠</span>
            <span className="wap-table-title">Server software and technology found</span>
            <span className="result-count-pill">{technologies.length} found</span>
          </div>
          <table className="wap-table">
            <thead>
              <tr>
                <th></th>
                <th>Software / Version</th>
                <th>Category</th>
              </tr>
            </thead>
            <tbody>
              {pagedTechs.map((t: any, i: number) => (
                <tr key={i} className={i % 2 === 0 ? 'wap-row-even' : 'wap-row-odd'}>
                  <td className="wap-icon-cell">
                    <div className="wap-icon-wrapper">
                      <TechIcon tech={t} />
                      <span className="wap-tech-fallback hidden">
                        {(t.name || '?')[0].toUpperCase()}
                      </span>
                    </div>
                  </td>
                  <td className="wap-name-cell">
                    <span className="wap-tech-name">{t.name}</span>
                    {t.version && <span className="wap-tech-version"> {t.version}</span>}
                  </td>
                  <td className="wap-cat-cell">
                    {(t.categories || []).map((c: any) => c.name).join(', ') || 'Other'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {totalPages > 1 && (
            <div className="wap-pagination">
              <button disabled={techPage === 0} onClick={() => setTechPage(techPage - 1)} className="wap-page-btn">‹</button>
              <span className="wap-page-info">{techPage + 1} / {totalPages}</span>
              <button disabled={techPage >= totalPages - 1} onClick={() => setTechPage(techPage + 1)} className="wap-page-btn">›</button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Sub-components (existing) ─────────────────────────────────────────────────

function AxePanel({ data }: { data: any }) {
  const axeData = data?.data ?? data;
  const violations: any[] = axeData?.violations ?? [];
  const summary: Record<string, number> = axeData?.impact_summary ?? {};
  const impactOrder = ['critical', 'serious', 'moderate', 'minor'];

  return (
    <div className="result-panel">
      <div className="result-panel-header">
        <span className="result-panel-icon">♿</span>
        <span className="result-panel-title">Accessibility Audit</span>
        <span className="result-count-pill">{violations.length} violations</span>
      </div>

      <div className="axe-summary">
        {impactOrder.map((impact) => {
          const cfg = IMPACT_CONFIG[impact];
          const count = summary[impact] ?? 0;
          return (
            <div key={impact} className={`axe-summary-badge ${cfg.cls}`}>
              <span className="axe-badge-label">{cfg.label}</span>
              <span className="axe-badge-count">{count}</span>
            </div>
          );
        })}
      </div>

      {axeData?.passes_count != null && (
        <div className="axe-passes">
          ✓ {axeData.passes_count} rules passed
          {axeData.inapplicable_count > 0 && (
            <span> · {axeData.inapplicable_count} not applicable</span>
          )}
        </div>
      )}

      {violations.length > 0 ? (
        <div className="axe-violations">
          {violations.map((v: any, i: number) => {
            const cfg = IMPACT_CONFIG[v.impact] ?? { label: v.impact, cls: 'impact-minor' };
            return (
              <div key={i} className="axe-violation-card">
                <div className="axe-violation-header">
                  <span className={`impact-pill ${cfg.cls}`}>{cfg.label}</span>
                  <span className="axe-violation-id">{v.id}</span>
                  {v.nodes_count > 1 && (
                    <span className="axe-violation-count">×{v.nodes_count}</span>
                  )}
                </div>
                <div className="axe-violation-help">{v.help}</div>
                {v.tags && v.tags.length > 0 && (
                  <div className="axe-violation-tags">
                    {v.tags.filter((t: string) => t.startsWith('wcag') || t.startsWith('best')).slice(0, 4).map((tag: string, ti: number) => (
                      <span key={ti} className="axe-tag">{tag}</span>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="axe-no-violations">✓ ไม่พบปัญหา Accessibility</div>
      )}
    </div>
  );
}

function LighthousePanel({ data }: { data: any }) {
  const lhData = data?.data ?? data;
  const categories: Record<string, { title: string; score: number | null }> = lhData?.categories ?? {};
  const failedAudits: any[] = lhData?.failed_audits ?? [];
  const categoryOrder = ['performance', 'accessibility', 'best-practices', 'seo'];
  const categoryIcons: Record<string, string> = {
    performance: '⚡', accessibility: '♿', 'best-practices': '✅', seo: '🔍',
  };

  return (
    <div className="result-panel">
      <div className="result-panel-header">
        <span className="result-panel-icon">📊</span>
        <span className="result-panel-title">Lighthouse Audit</span>
        {lhData?.lighthouse_version && (
          <span className="result-count-pill">v{lhData.lighthouse_version}</span>
        )}
      </div>

      <div className="lh-scores">
        {categoryOrder.map((key) => {
          const cat = categories[key];
          if (!cat) return null;
          const score = cat.score;
          return (
            <div key={key} className={`lh-score-card ${scoreColorClass(score)}`}>
              <div className="lh-score-icon">{categoryIcons[key]}</div>
              <div className="lh-score-value">{score ?? '—'}</div>
              <div className="lh-score-label">{cat.title}</div>
            </div>
          );
        })}
      </div>

      {failedAudits.length > 0 ? (
        <div className="lh-audits">
          <div className="lh-audits-header">Failed Audits ({lhData?.total_failed ?? failedAudits.length})</div>
          <div className="lh-audit-list">
            {failedAudits.map((audit: any, i: number) => (
              <div key={i} className="lh-audit-item">
                <span className={`lh-audit-score ${scoreColorClass(audit.score)}`}>
                  {audit.score}
                </span>
                <span className="lh-audit-title">{audit.title}</span>
                {audit.displayValue && (
                  <span className="lh-audit-value">{audit.displayValue}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="lh-all-pass">✓ All audits passed</div>
      )}
    </div>
  );
}

function WappalyzerPanel({ data }: { data: any }) {
  const techs: any[] = data?.data?.technologies ?? data?.technologies ?? [];
  const [techPage, setTechPage] = useState(0);
  const TECH_PER_PAGE = 10;

  if (!techs.length) {
    return <div className="result-empty">ไม่พบเทคโนโลยี หรือการสแกนล้มเหลว</div>;
  }

  const totalPages = Math.ceil(techs.length / TECH_PER_PAGE);
  const pagedTechs = techs.slice(techPage * TECH_PER_PAGE, (techPage + 1) * TECH_PER_PAGE);

  return (
    <div className="result-panel">
      <div className="result-panel-header">
        <span className="result-panel-icon">🛠</span>
        <span className="result-panel-title">Detected Technologies</span>
        <span className="result-count-pill">{techs.length} found</span>
      </div>
      <table className="wap-table">
        <thead>
          <tr>
            <th></th>
            <th>Software / Version</th>
            <th>Category</th>
          </tr>
        </thead>
        <tbody>
          {pagedTechs.map((t: any, i: number) => (
            <tr key={i} className={i % 2 === 0 ? 'wap-row-even' : 'wap-row-odd'}>
              <td className="wap-icon-cell">
                <div className="wap-icon-wrapper">
                  <TechIcon tech={t} />
                  <span className="wap-tech-fallback hidden">{(t.name || '?')[0].toUpperCase()}</span>
                </div>
              </td>
              <td className="wap-name-cell">
                <span className="wap-tech-name">{t.name}</span>
                {t.version && <span className="wap-tech-version"> {t.version}</span>}
              </td>
              <td className="wap-cat-cell">
                {(t.categories || []).map((c: any) => c.name).join(', ') || 'Other'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {totalPages > 1 && (
        <div className="wap-pagination">
          <button disabled={techPage === 0} onClick={() => setTechPage(techPage - 1)} className="wap-page-btn">‹</button>
          <span className="wap-page-info">{techPage + 1} / {totalPages}</span>
          <button disabled={techPage >= totalPages - 1} onClick={() => setTechPage(techPage + 1)} className="wap-page-btn">›</button>
        </div>
      )}
    </div>
  );
}

function ZapPanel({ data }: { data: any }) {
  if (data?.success === false) {
    return (
      <div className="result-panel result-panel--warn">
        <div className="result-panel-header">
          <span className="result-panel-icon">⚡</span>
          <span className="result-panel-title">ZAP Security Scan</span>
        </div>
        <div className="result-empty zap-unavailable">{data?.error ?? 'ZAP service unavailable'}</div>
      </div>
    );
  }

  const zapData = data?.data ?? data;
  const alerts: any[] = zapData?.alerts ?? [];
  const summary: Record<string, number> = zapData?.risk_summary ?? {};
  const riskOrder = ['High', 'Medium', 'Low', 'Informational'];

  return (
    <div className="result-panel">
      <div className="result-panel-header">
        <span className="result-panel-icon">⚡</span>
        <span className="result-panel-title">ZAP Security Scan</span>
        <span className="result-count-pill">{alerts.length} alerts</span>
      </div>

      <div className="zap-summary">
        {riskOrder.map((r) => {
          const cfg = RISK_CONFIG[r];
          const count = summary[r] ?? 0;
          return (
            <div key={r} className={`zap-summary-badge ${cfg.cls}`}>
              <span className="zap-badge-label">{cfg.label}</span>
              <span className="zap-badge-count">{count}</span>
            </div>
          );
        })}
      </div>

      {alerts.length > 0 ? (
        <div className="zap-table-wrap">
          <table className="zap-table">
            <thead>
              <tr>
                <th>Risk</th>
                <th>Alert</th>
                <th>URL Path</th>
                <th>Method</th>
              </tr>
            </thead>
            <tbody>
              {alerts.map((a: any, i: number) => {
                const cfg = RISK_CONFIG[a.risk] ?? { label: a.risk, cls: 'risk-info' };
                let path = '—';
                try { path = a.url ? new URL(a.url).pathname : '—'; } catch {}
                return (
                  <tr key={i}>
                    <td><span className={`risk-pill ${cfg.cls}`}>{cfg.label}</span></td>
                    <td className="alert-name">{a.alert ?? a.name}</td>
                    <td className="alert-url" title={a.url}>{path}</td>
                    <td className="alert-method">{a.method ?? '—'}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="zap-no-alerts">✓ ไม่พบช่องโหว่จากการสแกน</div>
      )}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function Home() {
  const [url, setUrl]               = useState('');
  const [result, setResult]         = useState<any>(null);
  const [loading, setLoading]       = useState(false);
  const [scanStatus, setScanStatus] = useState<'idle' | 'scanning' | 'done' | 'error'>('idle');
  const [scanType, setScanType]     = useState<ScanType>('standards');
  const [aiResult, setAiResult]     = useState<string | null>(null);
  const [aiLoading, setAiLoading]   = useState(false);
  const [aiError, setAiError]       = useState<string | null>(null);

  const runScan = async (type: string) => {
    const res = await fetch(`${API_BASE_URL}/scan/${type}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    });
    return res.json();
  };

  const handleScan = async () => {
    if (!url) return;
    setLoading(true);
    setResult(null);
    setAiResult(null);
    setAiError(null);
    setScanStatus('scanning');
    try {
      const data = await runScan(scanType);
      setResult(data);
      setScanStatus('done');
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
      const res = await fetch(`${API_BASE_URL}/analyze/ai`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, scan_data: result, scan_type: scanType }),
      });
      const data = await res.json();
      if (!res.ok || !data.success) {
        setAiError(data.detail || data.error || 'AI analysis failed');
      } else {
        setAiResult(data.analysis);
      }
    } catch {
      setAiError('ไม่สามารถเชื่อมต่อกับ AI service ได้');
    }
    setAiLoading(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && url && !loading) handleScan();
  };

  const getStatusText = () => {
    switch (scanStatus) {
      case 'idle':     return '> READY';
      case 'scanning': return scanType === 'standards'
        ? '> SCANNING ALL STANDARDS (this may take a few minutes)...'
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

  const formatAiText = (text: string) =>
    text.split('\n').map((line, i) => {
      if (line.startsWith('## '))  return <h3 key={i} className="ai-heading-2">{line.slice(3)}</h3>;
      if (line.startsWith('### ')) return <h4 key={i} className="ai-heading-3">{line.slice(4)}</h4>;
      if (line.startsWith('- **')) {
        const html = line.slice(2).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        return <li key={i} className="ai-list-item" dangerouslySetInnerHTML={{ __html: html }} />;
      }
      if (line.startsWith('- ')) return <li key={i} className="ai-list-item">{line.slice(2)}</li>;
      if (line.trim() === '') return <div key={i} className="ai-spacer" />;
      const html = line.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
      return <p key={i} className="ai-para" dangerouslySetInnerHTML={{ __html: html }} />;
    });

  const showResult = result && !result.error;

  return (
    <>
      <div className="crt-overlay" aria-hidden="true" />
      <div className="bg-orbs" aria-hidden="true" />

      <div className="page-wrapper">
        {/* Navbar */}
        <nav className="navbar fade-in" role="navigation" aria-label="Main navigation">
          <a href="/" className="navbar-brand" id="nav-home-link">
            <div className="navbar-logo" aria-hidden="true">W</div>
            <span className="navbar-title">WebScan</span>
          </a>
          <div className="navbar-right">
            <div className="navbar-status-dot" aria-hidden="true" />
            <span>ONLINE</span>
            <span className="navbar-badge">v1.0</span>
          </div>
        </nav>

        {/* Hero */}
        <section className="hero-section fade-in-delay-1" aria-labelledby="hero-heading">
          <div className="hero-eyebrow" aria-hidden="true">
            <span className="hero-eyebrow-dot" />
            AI-Assisted Security Assessment
          </div>
          <h1 className="hero-title" id="hero-heading">
            Web Standards{' '}
            <span className="hero-title-accent">Scanner</span>
            <span className="hero-cursor" aria-hidden="true" />
          </h1>
          <p className="hero-subtitle">
            วิเคราะห์เทคโนโลยีและมาตรฐานเว็บไซต์ของคุณอย่างรวดเร็ว ปลอดภัย และแม่นยำ
          </p>
        </section>

        {/* Scanner Card */}
        <main id="main-content">
          <section className="scanner-card fade-in-delay-2" aria-label="URL Scanner">
            <label htmlFor="url-input" className="scanner-label">
              // Target URL
            </label>

            <div className="scan-type-selector" id="scan-type-selector" role="group" aria-label="Scan type">
              {(['standards', 'wappalyzer', 'zap', 'axe', 'lighthouse'] as ScanType[]).map((type) => (
                <button
                  key={type}
                  id={`scan-type-${type}`}
                  className={`scan-type-btn ${scanType === type ? 'active' : ''}`}
                  onClick={() => setScanType(type)}
                  disabled={loading}
                  aria-pressed={scanType === type}
                >
                  {type === 'standards'    && '📋 STANDARDS'}
                  {type === 'wappalyzer'   && '🛠 WAPPALYZER'}
                  {type === 'zap'          && '⚡ ZAP SCAN'}
                  {type === 'axe'          && '♿ AXE A11Y'}
                  {type === 'lighthouse'   && '📊 LIGHTHOUSE'}
                </button>
              ))}
            </div>

            <div className="input-group">
              <input
                id="url-input"
                type="url"
                className="url-input"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="https://target.example.com"
                aria-label="URL ที่ต้องการสแกน"
                autoComplete="url"
                spellCheck={false}
              />
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

            {/* ── Results ── */}
            {showResult && (
              <div className="results-wrapper" id="scan-results">
                <div className="results-header">
                  <span className="results-title">// OUTPUT</span>
                </div>

                <div className="results-panels">
                  {scanType === 'standards' && <StandardsReportPanel data={result} />}
                  {scanType === 'wappalyzer' && <WappalyzerPanel data={result} />}
                  {scanType === 'zap' && <ZapPanel data={result} />}
                  {scanType === 'axe' && <AxePanel data={result} />}
                  {scanType === 'lighthouse' && <LighthousePanel data={result} />}
                </div>

                {/* AI Analysis Button */}
                <div className="ai-trigger-row">
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
                    <span className="ai-model-badge">llama3.2:3b · Ollama</span>
                  )}
                </div>

                {aiError && (
                  <div className="error-banner" role="alert" id="ai-error-message">
                    <span className="error-icon" aria-hidden="true">⚠</span>
                    <span>{aiError}</span>
                  </div>
                )}

                {aiResult && (
                  <div className="ai-panel" id="ai-report" aria-label="AI Security Analysis">
                    <div className="ai-panel-header">
                      <span className="ai-panel-title">// AI SECURITY REPORT</span>
                      <span className="ai-panel-url">{url}</span>
                    </div>
                    <div className="ai-panel-body">
                      {formatAiText(aiResult)}
                    </div>
                  </div>
                )}
              </div>
            )}
          </section>
        </main>

        {/* Features */}
        <section className="features-section fade-in-delay-3" aria-label="Features">
          <div className="features-grid">
            <article className="feature-card" id="feature-tech">
              <div className="feature-icon-wrap" aria-hidden="true">🛠</div>
              <h3 className="feature-title">Tech Detection</h3>
              <p className="feature-desc">
                วิเคราะห์ Framework, CMS, Library และเทคโนโลยีที่เว็บไซต์ใช้งาน
              </p>
            </article>
            <article className="feature-card" id="feature-security">
              <div className="feature-icon-wrap" aria-hidden="true">🔒</div>
              <h3 className="feature-title">Security Audit</h3>
              <p className="feature-desc">
                ตรวจหาช่องโหว่และจุดอ่อนด้านความปลอดภัยของเว็บไซต์
              </p>
            </article>
            <article className="feature-card" id="feature-ai">
              <div className="feature-icon-wrap" aria-hidden="true">✦</div>
              <h3 className="feature-title">AI Analysis</h3>
              <p className="feature-desc">
                วิเคราะห์ผลสแกนด้วย Ollama AI และรับรายงานความปลอดภัยแบบละเอียด
              </p>
            </article>
          </div>
        </section>

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