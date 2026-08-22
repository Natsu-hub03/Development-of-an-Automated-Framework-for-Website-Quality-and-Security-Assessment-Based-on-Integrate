'use client';
import { IMPACT_CONFIG } from '../../lib/constants';

export function AxePanel({ data }: { data: any }) {
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
