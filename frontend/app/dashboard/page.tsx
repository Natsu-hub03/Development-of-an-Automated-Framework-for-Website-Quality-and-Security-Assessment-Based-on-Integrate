'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';

const STANDARD_ICONS: Record<string, string> = {
  wcag: '♿',
  cwv: '📊',
  ncsa: '🛡️',
  owasp: '🔒',
};

function getGrade(pct: number): { label: string; cls: string } {
  if (pct >= 90) return { label: 'Excellent', cls: 'grade-excellent' };
  if (pct >= 70) return { label: 'Good', cls: 'grade-good' };
  if (pct >= 50) return { label: 'Fair', cls: 'grade-fair' };
  return { label: 'Needs Work', cls: 'grade-poor' };
}

// Extract all checks with a given status from standards data
function extractChecks(standards: any[], status: string) {
  const items: any[] = [];
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

function combineScanResults(resultsByType: Record<string, any>, currentDashboardData: any) {
  if (!resultsByType || Object.keys(resultsByType).length === 0) {
    return currentDashboardData;
  }

  // Determine active target URL
  const primaryUrl =
    (currentDashboardData?.data ?? currentDashboardData)?.url ||
    (resultsByType['standards']?.data ?? resultsByType['standards'])?.url ||
    Object.values(resultsByType)[0]?.data?.url ||
    Object.values(resultsByType)[0]?.url ||
    '';

  const normPrimary = primaryUrl.trim().replace(/\/+$/, '').toLowerCase();

  // If full 'standards' scan exists and matches primary URL, use that directly
  if (resultsByType['standards']) {
    const stdScan = resultsByType['standards'];
    const stdUrl = ((stdScan.data ?? stdScan).url || '').trim().replace(/\/+$/, '').toLowerCase();
    if (!normPrimary || !stdUrl || stdUrl === normPrimary) {
      return stdScan;
    }
  }

  // Otherwise, combine only individual scans that belong to the same target URL
  const stdKeys = ['wcag', 'cwv', 'ncsa', 'owasp'];
  const standardsList: any[] = [];
  const seenStdIds = new Set<string>();
  let totalP = 0;
  let totalF = 0;
  let totalW = 0;
  let totalItems = 0;
  let allTechs: any[] = [];
  let url = '';
  let timestamp = '';

  for (const k of stdKeys) {
    const raw = resultsByType[k];
    if (!raw) continue;
    const rData = raw.data ?? raw;
    const itemUrl = (rData.url || '').trim().replace(/\/+$/, '').toLowerCase();
    // Discard scans from different websites
    if (normPrimary && itemUrl && itemUrl !== normPrimary) {
      continue;
    }
    if (rData.url) url = rData.url;
    if (rData.timestamp) timestamp = rData.timestamp;
    if (rData.wappalyzer_technologies?.length) {
      allTechs = [...allTechs, ...rData.wappalyzer_technologies];
    }
    for (const std of (rData.standards ?? [])) {
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
      url: url || primaryUrl || (currentDashboardData?.data ?? currentDashboardData)?.url || '',
      timestamp: timestamp || (currentDashboardData?.data ?? currentDashboardData)?.timestamp || '',
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

  return currentDashboardData;
}

export default function DashboardPage() {
  const [data, setData] = useState<any>(null);
  const [mounted, setMounted] = useState(false);
  const [activeFilter, setActiveFilter] = useState<'all' | 'pass' | 'fail' | 'warning'>('all');
  const [expandedEvidence, setExpandedEvidence] = useState<Set<string>>(new Set());

  const toggleEvidence = (key: string) => {
    setExpandedEvidence((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  useEffect(() => {
    setMounted(true);
    try {
      const rawMap = localStorage.getItem('webscan_results_by_type');
      const rawDashboard = localStorage.getItem('webscan_dashboard_data');
      
      const map = rawMap ? JSON.parse(rawMap) : {};
      const dashboardData = rawDashboard ? JSON.parse(rawDashboard) : null;
      
      const combined = combineScanResults(map, dashboardData);
      if (combined) {
        setData(combined);
      }
    } catch {
      // ignore parse errors
    }
  }, []);

  if (!mounted) return null;

  // Empty state
  if (!data) {
    return (
      <>
        <div className="crt-overlay" aria-hidden="true" />
        <div className="bg-orbs" aria-hidden="true" />
        <div className="dashboard-page">
          <nav className="navbar" role="navigation">
            <Link href="/" className="navbar-brand">
              <div className="navbar-logo" aria-hidden="true">W</div>
              <span className="navbar-title">WebScan</span>
            </Link>
          </nav>
          <div className="dashboard-container">
            <div className="dash-empty">
              <div className="dash-empty-icon">📊</div>
              <div className="dash-empty-text">
                ยังไม่มีผลการสแกน กรุณาสแกนเว็บไซต์ก่อน
              </div>
              <Link href="/" className="dash-empty-btn">
                ◄ กลับไปสแกน
              </Link>
            </div>
          </div>
        </div>
      </>
    );
  }

  const reportData = data?.data ?? data;
  const summary = reportData?.summary ?? { total: 0, passed: 0, failed: 0, warning: 0 };
  const standards: any[] = reportData?.standards ?? [];
  const technologies: any[] = reportData?.wappalyzer_technologies ?? [];
  const url = reportData?.url ?? '';
  const timestamp = reportData?.timestamp ?? '';

  const totalChecks = summary.total || 1;
  const passRate = Math.round((summary.passed / totalChecks) * 100);
  const failRate = Math.round((summary.failed / totalChecks) * 100);
  const warnRate = Math.round((summary.warning / totalChecks) * 100);
  const grade = getGrade(passRate);

  const failedItems = extractChecks(standards, 'fail');
  const warningItems = extractChecks(standards, 'warning');
  const passedItems = extractChecks(standards, 'pass');

  const formattedTime = timestamp
    ? new Date(timestamp).toLocaleString('th-TH', {
        year: 'numeric', month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit',
      })
    : '';

  // Combine all items for "all" filter
  const allItems = [...failedItems, ...warningItems, ...passedItems];
  const filteredItems =
    activeFilter === 'all'
      ? allItems
      : activeFilter === 'pass'
        ? passedItems
        : activeFilter === 'fail'
          ? failedItems
          : warningItems;

  const STATUS_ICON: Record<string, string> = {
    pass: '✅',
    fail: '❌',
    warning: '⚠️',
  };

  return (
    <>
      <div className="crt-overlay" aria-hidden="true" />
      <div className="bg-orbs" aria-hidden="true" />

      <div className="dashboard-page">
        {/* Navbar */}
        <nav className="navbar fade-in" role="navigation" aria-label="Dashboard navigation">
          <Link href="/" className="navbar-brand" id="nav-home-link">
            <div className="navbar-logo" aria-hidden="true">W</div>
            <span className="navbar-title">WebScan</span>
          </Link>
          <div className="navbar-right">
            <div className="navbar-status-dot" aria-hidden="true" />
            <span>DASHBOARD</span>
            <span className="navbar-badge">v1.0</span>
          </div>
        </nav>

        <div className="dashboard-container">
          {/* Header */}
          <header className="dash-header fade-in">
            <div className="dash-header-left">
              <h1 className="dash-title">
                Scan <span className="dash-title-accent">Dashboard</span>
              </h1>
              {url && <div className="dash-url">{url}</div>}
              {formattedTime && <div className="dash-timestamp">🕐 {formattedTime}</div>}
            </div>
            <div className="dash-actions">
              <button
                className="dash-action-btn"
                onClick={() => window.print()}
                aria-label="พิมพ์รายงาน"
              >
                🖨️ PRINT
              </button>
              <Link href="/" className="dash-back-btn">
                ◄ BACK TO SCANNER
              </Link>
            </div>
          </header>

          {/* Overall Score Ring */}
          <section className="dash-score-section fade-in-delay-1" aria-label="Overall Score">
            <div className="dash-score-ring-wrap">
              <div
                className="dash-score-ring"
                style={{ '--score-pct': passRate } as React.CSSProperties}
              />
              <div className="dash-score-inner">
                <div className="dash-score-value">
                  {passRate}<span className="dash-score-unit">%</span>
                </div>
                <div className="dash-score-label">compliance</div>
                <div className={`dash-score-grade ${grade.cls}`}>
                  {grade.label}
                </div>
              </div>
            </div>
          </section>

          {/* Summary Stats */}
          <div className="dash-stats-grid" role="group" aria-label="Summary Statistics">
            <div className="dash-stat-card dash-stat-card--total">
              <div className="dash-stat-icon">📋</div>
              <div className="dash-stat-value">{summary.total}</div>
              <div className="dash-stat-label">รายการทั้งหมด</div>
              <div className="dash-stat-sub">{standards.length} มาตรฐาน</div>
            </div>
            <div className="dash-stat-card dash-stat-card--pass">
              <div className="dash-stat-icon">✅</div>
              <div className="dash-stat-value">{summary.passed}</div>
              <div className="dash-stat-label">ผ่าน</div>
              <div className="dash-stat-sub">{passRate}%</div>
            </div>
            <div className="dash-stat-card dash-stat-card--fail">
              <div className="dash-stat-icon">❌</div>
              <div className="dash-stat-value">{summary.failed}</div>
              <div className="dash-stat-label">ไม่ผ่าน</div>
              <div className="dash-stat-sub">{failRate}%</div>
            </div>
            <div className="dash-stat-card dash-stat-card--warn">
              <div className="dash-stat-icon">⚠️</div>
              <div className="dash-stat-value">{summary.warning}</div>
              <div className="dash-stat-label">เตือน</div>
              <div className="dash-stat-sub">{warnRate}%</div>
            </div>
          </div>

          {/* Per-Standard Gauge Cards */}
          <div className="dash-section">
            <div className="dash-section-title">// per-standard breakdown</div>
            <div className="dash-standards-grid">
              {standards.map((std: any) => {
                const stdPassRate = std.total > 0
                  ? Math.round((std.passed / std.total) * 100)
                  : 0;

                return (
                  <div key={std.id} className="dash-std-card">
                    <div className="dash-std-header">
                      <div className="dash-std-icon">
                        {STANDARD_ICONS[std.id] ?? '📋'}
                      </div>
                      <div className="dash-std-info">
                        <div className="dash-std-name">{std.name}</div>
                        <div className="dash-std-owner">{std.owner}</div>
                      </div>
                    </div>

                    <div className="dash-gauge-wrap">
                      <div
                        className="dash-gauge"
                        style={{ '--score-pct': stdPassRate } as React.CSSProperties}
                      />
                      <div className="dash-gauge-inner">
                        <div className="dash-gauge-value">
                          {stdPassRate}<span className="dash-gauge-unit">%</span>
                        </div>
                        <div className="dash-gauge-sub">{std.passed}/{std.total}</div>
                      </div>
                    </div>

                    <div className="dash-std-counts">
                      <div className="dash-std-count-item">
                        <div className="dash-std-count-dot dash-std-count-dot--pass" />
                        <span>{std.passed}</span>
                      </div>
                      <div className="dash-std-count-item">
                        <div className="dash-std-count-dot dash-std-count-dot--fail" />
                        <span>{std.failed}</span>
                      </div>
                      <div className="dash-std-count-item">
                        <div className="dash-std-count-dot dash-std-count-dot--warn" />
                        <span>{std.warning}</span>
                      </div>
                    </div>

                    <div className="dash-std-progress">
                      <div
                        className="dash-std-progress-fill"
                        style={{ width: `${stdPassRate}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Status Distribution Bar */}
          <div className="dash-section">
            <div className="dash-section-title">// status distribution</div>
            <div className="dash-dist-bar-wrap">
              <div className="dash-dist-bar">
                {passRate > 0 && (
                  <div
                    className="dash-dist-segment dash-dist-segment--pass"
                    style={{ width: `${passRate}%` }}
                  >
                    {passRate > 8 ? `${summary.passed}` : ''}
                  </div>
                )}
                {failRate > 0 && (
                  <div
                    className="dash-dist-segment dash-dist-segment--fail"
                    style={{ width: `${failRate}%` }}
                  >
                    {failRate > 8 ? `${summary.failed}` : ''}
                  </div>
                )}
                {warnRate > 0 && (
                  <div
                    className="dash-dist-segment dash-dist-segment--warn"
                    style={{ width: `${warnRate}%` }}
                  >
                    {warnRate > 8 ? `${summary.warning}` : ''}
                  </div>
                )}
              </div>

              <div className="dash-dist-legend">
                <div className="dash-dist-legend-item">
                  <div className="dash-dist-legend-dot dash-dist-legend-dot--pass" />
                  ผ่าน {summary.passed}
                </div>
                <div className="dash-dist-legend-item">
                  <div className="dash-dist-legend-dot dash-dist-legend-dot--fail" />
                  ไม่ผ่าน {summary.failed}
                </div>
                <div className="dash-dist-legend-item">
                  <div className="dash-dist-legend-dot dash-dist-legend-dot--warn" />
                  เตือน {summary.warning}
                </div>
              </div>

              {/* Per-standard bar rows */}
              <div className="dash-std-bars">
                {standards.map((std: any) => {
                  const p = std.total > 0 ? Math.round((std.passed / std.total) * 100) : 0;
                  const f = std.total > 0 ? Math.round((std.failed / std.total) * 100) : 0;
                  const w = std.total > 0 ? (100 - p - f) : 0;

                  return (
                    <div key={std.id} className="dash-std-bar-row">
                      <div className="dash-std-bar-label">
                        {STANDARD_ICONS[std.id]} {std.name}
                      </div>
                      <div className="dash-std-bar-track">
                        {p > 0 && (
                          <div
                            className="dash-dist-segment dash-dist-segment--pass"
                            style={{ width: `${p}%` }}
                          />
                        )}
                        {f > 0 && (
                          <div
                            className="dash-dist-segment dash-dist-segment--fail"
                            style={{ width: `${f}%` }}
                          />
                        )}
                        {w > 0 && (
                          <div
                            className="dash-dist-segment dash-dist-segment--warn"
                            style={{ width: `${w}%` }}
                          />
                        )}
                      </div>
                      <div className="dash-std-bar-pct">{p}%</div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* ═══ Filter Tabs + All Checklist Items ═══ */}
          <div className="dash-section">
            <div className="dash-section-title">// checklist details</div>
            <div className="dash-filter-tabs">
              <button
                className={`dash-filter-tab ${activeFilter === 'all' ? 'dash-filter-tab--active' : ''}`}
                onClick={() => setActiveFilter('all')}
              >
                📋 ทั้งหมด <span className="dash-filter-tab-count">{allItems.length}</span>
              </button>
              <button
                className={`dash-filter-tab dash-filter-tab--fail ${activeFilter === 'fail' ? 'dash-filter-tab--active' : ''}`}
                onClick={() => setActiveFilter('fail')}
              >
                ❌ ไม่ผ่าน <span className="dash-filter-tab-count">{failedItems.length}</span>
              </button>
              <button
                className={`dash-filter-tab dash-filter-tab--warn ${activeFilter === 'warning' ? 'dash-filter-tab--active' : ''}`}
                onClick={() => setActiveFilter('warning')}
              >
                ⚠️ เตือน <span className="dash-filter-tab-count">{warningItems.length}</span>
              </button>
              <button
                className={`dash-filter-tab dash-filter-tab--pass ${activeFilter === 'pass' ? 'dash-filter-tab--active' : ''}`}
                onClick={() => setActiveFilter('pass')}
              >
                ✅ ผ่าน <span className="dash-filter-tab-count">{passedItems.length}</span>
              </button>
            </div>

            <div className="dash-checklist-wrap">
              {filteredItems.length > 0 ? (
                <div className="dash-checklist-list">
                  {filteredItems.map((item, i) => {
                    const evKey = `${item.id}-${i}`;
                    const isEvidenceOpen = expandedEvidence.has(evKey);
                    const hasEvidence = item.evidence && item.evidence.length > 0;

                    return (
                      <div
                        key={evKey}
                        className={`dash-checklist-item dash-checklist-item--${item.status}`}
                      >
                        <div className="dash-checklist-item-main">
                          <span className="dash-checklist-status-icon">
                            {STATUS_ICON[item.status] ?? '⚠️'}
                          </span>
                          <span className="dash-failed-std-badge">
                            {STANDARD_ICONS[item.standardId]} {item.standardId}
                          </span>
                          <div className="dash-failed-info">
                            <div className="dash-failed-name">
                              {item.name}
                              <span className="dash-item-id-pill">{item.id}</span>
                            </div>
                            {item.name_th && (
                              <div className="dash-failed-name-th">{item.name_th}</div>
                            )}
                            {item.detail && (
                              <div className="dash-failed-detail">
                                <span className="dash-detail-tag">ผลการตรวจ:</span> {item.detail}
                              </div>
                            )}

                            {/* 🔍 เหตุผล / ความสำคัญ (ภาษาไทย) */}
                            {item.why_th && (
                              <div className="dash-why-box">
                                <span className="dash-why-icon">🔍</span>
                                <span className="dash-why-text">
                                  <strong>เหตุผล:</strong> {item.why_th}
                                </span>
                              </div>
                            )}

                            {/* 💡 วิธีแก้ไขแนะนำ (ภาษาไทย) สำหรับข้อที่ไม่ผ่านหรือเตือน */}
                            {item.status !== 'pass' && item.remediation_th && (
                              <div className="dash-fix-box">
                                <span className="dash-fix-icon">💡</span>
                                <span className="dash-fix-text">
                                  <strong>วิธีแก้ไข:</strong> {item.remediation_th}
                                </span>
                              </div>
                            )}

                            {/* Action Buttons Row */}
                            {hasEvidence && (
                              <div className="dash-item-actions">
                                <button
                                  className={`dash-evidence-toggle ${isEvidenceOpen ? 'dash-evidence-toggle--open' : ''}`}
                                  onClick={() => toggleEvidence(evKey)}
                                  aria-label="ดูตำแหน่งโค้ดและหลักฐาน"
                                  title="ดูตำแหน่งโค้ด & Selector"
                                >
                                  📍 <span>{item.status === 'pass' ? 'ดูโค้ดที่ผ่าน' : 'ดูตำแหน่งโค้ด'} ({item.evidence.length})</span>
                                  <span className={`dash-evidence-arrow ${isEvidenceOpen ? 'rotated' : ''}`}>▼</span>
                                </button>
                              </div>
                            )}
                          </div>
                        </div>

                        {/* 📍 Evidence Panel (Pass / Fail / Warn) */}
                        {hasEvidence && isEvidenceOpen && (
                          <div className="dash-evidence-panel">
                            <div className="dash-evidence-title">
                              📍 {item.status === 'pass' ? 'โค้ด/ข้อมูลที่ตรวจสอบผ่าน' : 'ตำแหน่งโค้ดที่ตรวจพบข้อบกพร่อง'}
                            </div>
                            {item.evidence.map((ev: any, ei: number) => (
                              <div key={ei} className="dash-evidence-node">
                                {/* CSS Selector / Location */}
                                {ev.target && ev.target.length > 0 && (
                                  <div className="dash-evidence-selector">
                                    <span className="dash-evidence-label">ตำแหน่ง / Selector:</span>
                                    <code className="dash-evidence-code">
                                      {Array.isArray(ev.target) ? ev.target.join(' > ') : ev.target}
                                    </code>
                                  </div>
                                )}
                                {/* HTML Snippet / Header value */}
                                {ev.html && (
                                  <div className="dash-evidence-html">
                                    <span className="dash-evidence-label">โค้ด / ข้อมูลที่พบ:</span>
                                    <pre className="dash-evidence-pre"><code>{ev.html}</code></pre>
                                  </div>
                                )}
                                {/* Summary / Note */}
                                {(ev.failureSummary || ev.passed_summary || ev.summary) && (
                                  <div className="dash-evidence-summary">
                                    <span className="dash-evidence-label">รายละเอียด:</span>
                                    <span className="dash-evidence-reason">
                                      {ev.failureSummary || ev.passed_summary || ev.summary}
                                    </span>
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="dash-failed-none">ไม่พบรายการในหมวดนี้</div>
              )}
            </div>
          </div>

          {/* Tech Stack */}
          {technologies.length > 0 && (
            <div className="dash-section">
              <div className="dash-section-title">// 🛠 detected technologies ({technologies.length})</div>
              <div className="dash-tech-grid">
                {technologies.map((tech: any, i: number) => {
                  const iconUrl = tech.icon
                    ? `https://www.wappalyzer.com/images/icons/${tech.icon}`
                    : null;

                  return (
                    <div key={i} className="dash-tech-card">
                      <div className="dash-tech-icon-box">
                        {iconUrl ? (
                          <img
                            src={iconUrl}
                            alt={tech.name}
                            onError={(e) => {
                              (e.target as HTMLImageElement).style.display = 'none';
                              const parent = (e.target as HTMLElement).parentElement;
                              const fallback = parent?.querySelector('.dash-tech-fallback-letter');
                              if (fallback) (fallback as HTMLElement).style.display = 'flex';
                            }}
                          />
                        ) : null}
                        <span
                          className="dash-tech-fallback-letter"
                          style={{ display: iconUrl ? 'none' : 'flex' }}
                        >
                          {(tech.name || '?')[0].toUpperCase()}
                        </span>
                      </div>
                      <div className="dash-tech-info">
                        <div className="dash-tech-name">
                          {tech.name}
                          {tech.version && (
                            <span className="dash-tech-version"> {tech.version}</span>
                          )}
                        </div>
                        <div className="dash-tech-cat">
                          {(tech.categories || []).map((c: any) => c.name).join(', ') || 'Other'}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Footer */}
          <footer className="footer" id="site-footer">
            <p>
              © 2026 WebScan &mdash; AI-Assisted Web Standards &amp; Vulnerability Assessment
            </p>
          </footer>
        </div>
      </div>
    </>
  );
}
