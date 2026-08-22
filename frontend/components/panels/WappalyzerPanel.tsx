'use client';
import { useState } from 'react';
import { TechIcon } from './StandardsReportPanel';
import { Technology } from '../../lib/types';

export function WappalyzerPanel({ data }: { data: any }) {
  const techs: Technology[] = data?.data?.technologies ?? data?.technologies ?? [];
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
