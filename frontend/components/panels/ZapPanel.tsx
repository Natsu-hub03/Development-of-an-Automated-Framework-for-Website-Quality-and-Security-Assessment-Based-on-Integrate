'use client';
import { RISK_CONFIG } from '../../lib/constants';

export function ZapPanel({ data }: { data: any }) {
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
          const cfg = RISK_CONFIG[r] ?? { label: r, cls: 'risk-info' };
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
