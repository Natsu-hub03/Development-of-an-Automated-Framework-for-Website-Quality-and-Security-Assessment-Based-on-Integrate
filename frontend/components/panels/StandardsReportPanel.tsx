'use client';
import { useState } from 'react';
import { STATUS_CONFIG, STANDARD_ICONS } from '../../lib/constants';
import { Technology, CheckStatus } from '../../lib/types';

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

export function StandardsReportPanel({ data }: { data: any }) {
  const reportData = data?.data ?? data;
  const standards: any[] = reportData?.standards ?? [];
  const summary = reportData?.summary ?? {};
  const technologies: Technology[] = reportData?.wappalyzer_technologies ?? [];
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
                          const statusKey = (check.status as CheckStatus) || 'warning';
                          const cfg = STATUS_CONFIG[statusKey] ?? STATUS_CONFIG.warning;
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
