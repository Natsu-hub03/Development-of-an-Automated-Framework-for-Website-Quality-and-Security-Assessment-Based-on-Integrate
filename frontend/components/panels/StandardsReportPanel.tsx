'use client';
import { useState } from 'react';
import { STATUS_CONFIG, STANDARD_ICONS } from '../../lib/constants';
import type { Technology, CheckStatus, ScanApiResponse, StandardsReportData, StandardReport, CategoryGroup, CheckItem } from '../../lib/types';
import { unwrapReportData } from '../../lib/utils';

export function TechIcon({ tech }: { tech: Technology }) {
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

export function StandardsReportPanel({
  data,
  expandedMap = {},
  onToggleStd,
}: {
  data: ScanApiResponse | StandardsReportData | Record<string, unknown> | null;
  expandedMap?: Record<string, boolean>;
  onToggleStd?: (id: string, isExp: boolean) => void;
}) {
  const reportData = unwrapReportData(data as ScanApiResponse);
  const rawObj = data as Record<string, unknown> | null;
  let standards: StandardReport[] = reportData?.standards ?? [];
  if (!standards.length && rawObj?.standard) {
    standards = [rawObj.standard as StandardReport];
  }

  const summary = reportData?.summary ?? (standards.length === 1 ? {
    total: standards[0].total ?? (standards[0].categories?.flatMap(c => c.checks).length || 0),
    passed: standards[0].passed ?? 0,
    failed: standards[0].failed ?? 0,
    warning: standards[0].warning ?? 0,
  } : { total: 71, passed: 0, failed: 0, warning: 0 });

  const technologies: Technology[] = reportData?.wappalyzer_technologies ?? [];
  const [internalExpanded, setInternalExpanded] = useState<string | null>(null);
  const [techPage, setTechPage] = useState(0);
  const TECH_PER_PAGE = 10;

  const isExpanded = (stdId: string) => {
    if (expandedMap && expandedMap[stdId] !== undefined) {
      return expandedMap[stdId];
    }
    if (onToggleStd) {
      return standards.length === 1;
    }
    return internalExpanded === stdId;
  };

  const toggleStd = (stdId: string) => {
    if (onToggleStd) {
      onToggleStd(stdId, !isExpanded(stdId));
    } else {
      setInternalExpanded(internalExpanded === stdId ? null : stdId);
    }
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
          // {standards.length === 1 ? `${standards[0].name.toUpperCase()} REPORT` : 'STANDARDS COMPLIANCE REPORT'}
        </div>
        <div className="standards-summary-stats">
          <div className="stat-card stat-total">
            <div className="stat-value">{summary.total ?? (standards.length === 1 ? standards[0].total : 71)}</div>
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
        {standards.map((std: StandardReport) => {
          const open = isExpanded(std.id);
          const passRate = std.total > 0
            ? Math.round((std.passed / std.total) * 100)
            : 0;

          return (
            <div key={std.id} className={`standard-card ${open ? 'expanded' : ''}`}>
              <button
                className="standard-card-header"
                onClick={() => toggleStd(std.id)}
                aria-expanded={open}
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
                  <span className={`standard-expand-icon ${open ? 'rotated' : ''}`}>▼</span>
                </div>
              </button>

              {open && (
                <div className="standard-card-body">
                  {(std.categories ?? []).map((cat: CategoryGroup) => (
                    <div key={cat.name} className="checklist-category">
                      <div className="checklist-category-name">{cat.name}</div>
                      <div className="checklist-items">
                        {(cat.checks ?? []).map((check: CheckItem) => {
                          const statusKey = (check.status as CheckStatus) || 'warning';
                          const cfg = STATUS_CONFIG[statusKey] ?? STATUS_CONFIG.warning;
                          const showRisk = statusKey === 'fail' || statusKey === 'warning';
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
                                {showRisk && (check.why_th || check.remediation_th) && (
                                  <div className={`checklist-risk-block ${statusKey === 'fail' ? 'risk-fail' : 'risk-warning'}`}>
                                    {check.why_th && (
                                      <div className="checklist-risk-row">
                                        <span className="checklist-risk-icon">⚡</span>
                                        <div>
                                          <div className="checklist-risk-label">ความเสี่ยง</div>
                                          <div className="checklist-risk-text">{check.why_th}</div>
                                        </div>
                                      </div>
                                    )}
                                    {check.remediation_th && (
                                      <div className="checklist-risk-row">
                                        <span className="checklist-risk-icon">🛠️</span>
                                        <div>
                                          <div className="checklist-risk-label">แนวทางแก้ไข</div>
                                          <div className="checklist-risk-text">{check.remediation_th}</div>
                                        </div>
                                      </div>
                                    )}
                                  </div>
                                )}
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
              {pagedTechs.map((t: Technology, i: number) => (
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
                    {(t.categories || []).map((c) => c.name).join(', ') || 'Other'}
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
