'use client';
import { scoreColorClass } from '../../lib/constants';

export function LighthousePanel({ data }: { data: any }) {
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
