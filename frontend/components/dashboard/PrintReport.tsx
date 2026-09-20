'use client';
import React from 'react';
import type { StandardsReportData, CheckItem, Technology } from '../../lib/types';
import { extractChecks } from '../../lib/utils';
import { getGrade } from '../../lib/constants';

interface PrintReportProps {
  data: StandardsReportData;
}

export function PrintReport({ data }: PrintReportProps) {
  const url = data.url || 'https://target.website';
  const timestamp = data.timestamp;
  const summary = data.summary || { total: 0, passed: 0, failed: 0, warning: 0 };
  const standards = data.standards || [];
  const technologies: Technology[] = data.wappalyzer_technologies || [];

  const totalChecks = summary.total || 1;
  const passRate = Math.round((summary.passed / totalChecks) * 100);
  const grade = getGrade(passRate);

  const failedItems = extractChecks(standards, 'fail');
  const warningItems = extractChecks(standards, 'warning');
  const passedItems = extractChecks(standards, 'pass');
  const nonPassedItems = [...failedItems, ...warningItems];

  // Separate security checks (OWASP / NCSA) from web standards (WCAG / CWV)
  const isSecurity = (item: CheckItem) => item.standardId === 'owasp' || item.standardId === 'ncsa';
  const isStandards = (item: CheckItem) => item.standardId === 'wcag' || item.standardId === 'cwv';

  const securityFailed = failedItems.filter(isSecurity);
  const securityWarning = warningItems.filter(isSecurity);
  const standardsFailed = failedItems.filter(isStandards);
  const standardsWarning = warningItems.filter(isStandards);

  // All checks for coverage list
  const allChecks: CheckItem[] = [...failedItems, ...warningItems, ...passedItems];

  // Determine Security Risk Level (Configuration & Vulnerability Assessment)
  // Headers & config scanner doesn't have active RCE/SQLi exploits (Critical = 0)
  // Missing security headers (HSTS, CSP, etc.) are Low or Medium risk misconfigurations
  let riskLevel = 'Low';
  let riskClass = 'low';
  if (securityFailed.length === 0 && securityWarning.length === 0) {
    riskLevel = 'Safe';
    riskClass = 'safe';
  } else if (securityFailed.length <= 4) {
    riskLevel = 'Low';
    riskClass = 'low';
  } else {
    riskLevel = 'Medium';
    riskClass = 'medium';
  }

  let targetHostname = '';
  try {
    targetHostname = new URL(url).hostname;
  } catch {
    targetHostname = url;
  }

  const formattedTime = timestamp
    ? new Date(timestamp).toLocaleString('en-US', {
        month: 'short',
        day: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
      }) + ' UTC'
    : new Date().toLocaleDateString();

  return (
    <article className="print-report-container">
      {/* ── Brand & Report Title ───────────────────────────────── */}
      <header className="print-brand-header">
        <div className="print-brand-left">
          <div className="print-logo-box">
            <span className="print-shield-icon">🛡️</span>
            <div className="print-brand-text">
              <span className="print-brand-name">WebScan</span>
              <span className="print-brand-sub">Security & Standards System</span>
            </div>
          </div>
        </div>
        <div className="print-report-type-badge">Official Audit Report</div>
      </header>

      <h1 className="print-main-title">Website Vulnerability & Standards Report</h1>
      <p className="print-main-subtitle">
        Automated Security & Standards Compliance Assessment (OWASP, WCAG 2.1, NCSA, Web Vitals)
      </p>

      {/* ── Target URL Banner ──────────────────────────────────── */}
      <div className="print-target-banner">
        <span className="print-target-check">✓</span>
        {targetHostname && (
          <img
            src={`https://www.google.com/s2/favicons?domain=${targetHostname}&sz=32`}
            alt=""
            className="print-target-favicon"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = 'none';
            }}
          />
        )}
        <span className="print-target-url">{url}</span>
      </div>

      {/* ── Summary Block ──────────────────────────────────────── */}
      <section className="print-section">
        <h2 className="print-section-heading">Summary</h2>

        <div className="print-summary-grid">
          {/* Box 1: Overall Risk Level */}
          <div className="print-summary-box print-overall-box">
            <div className="print-box-label">Overall risk level:</div>
            <div className={`print-overall-pill print-overall-pill--${riskClass}`}>
              {riskLevel}
            </div>
            <div className="print-overall-score">
              Security: <strong>{riskLevel} Risk</strong>
            </div>
            <div className="print-overall-score">
              Standards: <strong>{passRate}%</strong> ({grade.label})
            </div>
          </div>

          {/* Box 2: Risk & Compliance Ratings Table */}
          <div className="print-summary-box print-ratings-box">
            <div className="print-box-label">Risk & Compliance ratings:</div>
            <table className="print-ratings-table">
              <tbody>
                <tr>
                  <td className="rating-label">Critical Vulnerabilities:</td>
                  <td className="rating-count-cell">
                    <span className="rating-pill rating-pill--critical-zero">0</span>
                  </td>
                </tr>
                <tr>
                  <td className="rating-label">Security Misconfig (Med/Low):</td>
                  <td className="rating-count-cell">
                    <span className="rating-pill rating-pill--medium">{securityFailed.length + securityWarning.length}</span>
                  </td>
                </tr>
                <tr>
                  <td className="rating-label">Standards / WCAG Issues:</td>
                  <td className="rating-count-cell">
                    <span className="rating-pill rating-pill--standards">{standardsFailed.length}</span>
                  </td>
                </tr>
                <tr>
                  <td className="rating-label">Passed Checks:</td>
                  <td className="rating-count-cell">
                    <span className="rating-pill rating-pill--pass">{summary.passed}</span>
                  </td>
                </tr>
                <tr>
                  <td className="rating-label">Total Checks Evaluated:</td>
                  <td className="rating-count-cell">
                    <span className="rating-pill rating-pill--total">{summary.total}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Box 3: Scan Information */}
          <div className="print-summary-box print-info-box">
            <div className="print-box-label">Scan information:</div>
            <table className="print-info-table">
              <tbody>
                <tr>
                  <td className="info-label">Target:</td>
                  <td className="info-val info-val-url">{url}</td>
                </tr>
                <tr>
                  <td className="info-label">Scan time:</td>
                  <td className="info-val">{formattedTime}</td>
                </tr>
                <tr>
                  <td className="info-label">Tests performed:</td>
                  <td className="info-val">{summary.total} checks</td>
                </tr>
                <tr>
                  <td className="info-label">Scan status:</td>
                  <td className="info-val">
                    <span className="print-status-finished">Finished</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* ── Findings Section ───────────────────────────────────── */}
      <section className="print-section print-findings-section">
        <h2 className="print-section-heading">Findings</h2>

        {nonPassedItems.length === 0 ? (
          <div className="print-no-findings">
            ✓ ไม่พบช่องโหว่หรือข้อผิดพลาดร้ายแรง (All evaluated checks passed)
          </div>
        ) : (
          <div className="print-findings-list">
            {nonPassedItems.map((item, idx) => {
              const isSec = isSecurity(item);
              const isFail = item.status === 'fail';
              const firstEvidence = item.evidence?.[0];

              const badgeText = isSec
                ? (isFail ? 'SECURITY / CONFIRMED' : 'SECURITY / WARNING')
                : 'STANDARDS / NON-COMPLIANT';
              const badgeCls = isSec
                ? (isFail ? 'badge-confirmed' : 'badge-warning')
                : 'badge-standards';

              return (
                <div key={idx} className="print-finding-card">
                  {/* Finding Header */}
                  <div className="print-finding-top">
                    <div className="print-finding-title-wrap">
                      <span className="print-finding-flag">{isSec ? '🚩' : '📋'}</span>
                      <span className="print-finding-title">{item.name}</span>
                      {item.name_th && (
                        <span className="print-finding-title-th"> ({item.name_th})</span>
                      )}
                    </div>
                    <span className={`print-finding-badge ${badgeCls}`}>
                      {badgeText}
                    </span>
                  </div>

                  <div className="print-finding-sub">
                    {isSec ? 'Security Assessment' : 'Web Accessibility & Standards (WCAG / SEO)'} &bull; {item.standardName || item.standardId} &bull; {item.id}
                  </div>

                  {/* Finding Table */}
                  <table className="print-finding-table">
                    <thead>
                      <tr>
                        <th style={{ width: '28%' }}>URL</th>
                        <th style={{ width: '24%' }}>Method / Standard</th>
                        <th style={{ width: '48%' }}>Evidence</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td className="print-table-url">{url}</td>
                        <td>
                          <strong>GET</strong>
                          <div className="print-table-std">{item.standardId || item.standard}</div>
                        </td>
                        <td className="print-table-evidence">
                          {item.detail && (
                            <div className="print-evidence-detail">{item.detail}</div>
                          )}
                          {firstEvidence?.html && (
                            <div className="print-evidence-code-box">
                              <pre className="print-evidence-pre">
                                <code>{firstEvidence.html}</code>
                              </pre>
                            </div>
                          )}
                          {firstEvidence?.target && (
                            <div className="print-evidence-selector">
                              Selector: <code>{Array.isArray(firstEvidence.target) ? firstEvidence.target.join(' > ') : firstEvidence.target}</code>
                            </div>
                          )}
                        </td>
                      </tr>
                    </tbody>
                  </table>

                  {/* Details Box */}
                  <div className="print-finding-details">
                    <div className="print-details-head">▼ Details</div>

                    {item.why_th && (
                      <div className="print-detail-block">
                        <div className="print-detail-title">
                          {isSec ? 'Risk description:' : 'Standards impact (ผลกระทบด้านมาตรฐานและการใช้งาน):'}
                        </div>
                        <div className="print-detail-body">{item.why_th}</div>
                      </div>
                    )}

                    {item.remediation_th && (
                      <div className="print-detail-block">
                        <div className="print-detail-title">Recommendation:</div>
                        <div className="print-detail-body">{item.remediation_th}</div>
                      </div>
                    )}

                    <div className="print-detail-block">
                      <div className="print-detail-title">Classification:</div>
                      <div className="print-classification-list">
                        <div>Check ID : <strong>{item.id}</strong></div>
                        <div>Standard : <strong>{item.standardName || item.standardId}</strong></div>
                        {item.category && <div>Category : {item.category}</div>}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* ── Server Software and Technology Found ──────────────── */}
      {technologies.length > 0 && (
        <section className="print-section print-tech-section">
          <div className="print-section-heading-row">
            <h2 className="print-section-heading">🛠️ Server software and technology found</h2>
            <span className="print-heading-pill">port 443/tcp</span>
          </div>

          <table className="print-tech-table">
            <thead>
              <tr>
                <th style={{ width: '50%' }}>Software / Version</th>
                <th style={{ width: '50%' }}>Category</th>
              </tr>
            </thead>
            <tbody>
              {technologies.map((t, i) => {
                const icon = t.icon;
                const iconUrl = icon
                  ? (icon.startsWith('http') ? icon : `https://www.wappalyzer.com/images/icons/${icon}`)
                  : null;
                const initial = (t.name || '?').charAt(0).toUpperCase();

                return (
                  <tr key={i} className={i % 2 === 0 ? 'row-even' : ''}>
                    <td className="tech-name-cell">
                      <div className="print-tech-name-with-icon">
                        <div className="print-tech-icon-wrap">
                          {iconUrl ? (
                            <img
                              src={iconUrl}
                              alt={t.name}
                              className="print-tech-icon-img"
                              onError={(e) => {
                                const target = e.target as HTMLImageElement;
                                target.style.display = 'none';
                                const parent = target.parentElement;
                                const fallback = parent?.querySelector('.print-tech-icon-fallback');
                                if (fallback) (fallback as HTMLElement).style.display = 'flex';
                              }}
                            />
                          ) : null}
                          <span
                            className="print-tech-icon-fallback"
                            style={{ display: iconUrl ? 'none' : 'flex' }}
                          >
                            {initial}
                          </span>
                        </div>
                        <span className="print-tech-label">
                          <strong>{t.name}</strong>
                          {t.version && <span className="tech-version-pill"> {t.version}</span>}
                        </span>
                      </div>
                    </td>
                    <td className="tech-cat-cell">
                      {(t.categories || []).map((c) => c.name).join(', ') || 'Miscellaneous'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </section>
      )}

      {/* ── Scan Coverage Information ─────────────────────────── */}
      <section className="print-section print-coverage-section">
        <h2 className="print-section-heading">Scan coverage information</h2>
        <div className="print-coverage-title-sub">
          List of tests performed ({totalChecks} checks across 4 standards)
        </div>

        <div className="print-coverage-standards-wrap">
          {standards.map((std) => {
            const stdChecks = std.categories?.flatMap((c) => c.checks) || [];
            const stdIcon = std.id === 'owasp' ? '🔒' : std.id === 'ncsa' ? '🛡️' : std.id === 'wcag' ? '♿' : '📊';

            return (
              <div key={std.id} className="print-coverage-std-block">
                <div className="print-cov-std-header">
                  <div className="print-cov-std-title">
                    <span className="print-cov-std-icon">{stdIcon}</span>
                    <strong>{std.name}</strong>
                    <span className="print-cov-std-count">({stdChecks.length} tests)</span>
                  </div>
                  <div className="print-cov-std-stats">
                    <span className="cov-badge cov-badge--pass">✓ {std.passed} ผ่าน</span>
                    {std.failed > 0 && <span className="cov-badge cov-badge--fail">✗ {std.failed} ไม่ผ่าน</span>}
                    {std.warning > 0 && <span className="cov-badge cov-badge--warn">⚠ {std.warning} เตือน</span>}
                  </div>
                </div>

                <div className="print-coverage-grid">
                  {stdChecks.map((chk, i) => {
                    const isPass = chk.status === 'pass';
                    const isFail = chk.status === 'fail';

                    return (
                      <div key={i} className={`print-coverage-item print-cov-status--${chk.status}`}>
                        <span className={`print-cov-icon ${isPass ? 'cov-icon-pass' : isFail ? 'cov-icon-fail' : 'cov-icon-warn'}`}>
                          {isPass ? '✓' : isFail ? '✗' : '⚠'}
                        </span>
                        <span className="print-cov-name">{chk.name}</span>
                        <span className={`print-cov-pill print-cov-pill--${chk.status}`}>
                          {isPass ? 'PASS' : isFail ? 'FAIL' : 'WARN'}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* ── Scan Parameters & Stats ───────────────────────────── */}
      <section className="print-section print-stats-footer-section">
        <div className="print-stats-footer-grid">
          <div className="print-footer-box">
            <h3 className="print-box-subtitle">Scan parameters</h3>
            <table className="print-footer-table">
              <tbody>
                <tr>
                  <td>target:</td>
                  <td className="bold-cell">{url}</td>
                </tr>
                <tr>
                  <td>scan_type:</td>
                  <td>Light & Full Web Standards</td>
                </tr>
                <tr>
                  <td>authentication:</td>
                  <td>False</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="print-footer-box">
            <h3 className="print-box-subtitle">Scan stats</h3>
            <table className="print-footer-table">
              <tbody>
                <tr>
                  <td>Total tests performed:</td>
                  <td className="bold-cell">{summary.total}</td>
                </tr>
                <tr>
                  <td>Passed checks:</td>
                  <td className="bold-cell text-pass">{summary.passed}</td>
                </tr>
                <tr>
                  <td>Failed checks:</td>
                  <td className="bold-cell text-fail">{summary.failed}</td>
                </tr>
                <tr>
                  <td>Warning checks:</td>
                  <td className="bold-cell text-warn">{summary.warning}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* ── Report Footer ─────────────────────────────────────── */}
      <footer className="print-page-footer">
        <span>WebScan &bull; Automated Web Standards &amp; Vulnerability Assessment System</span>
        <span>Generated: {formattedTime}</span>
      </footer>
    </article>
  );
}
