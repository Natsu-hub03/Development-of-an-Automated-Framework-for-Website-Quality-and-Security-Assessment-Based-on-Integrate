'use client';
import { useEffect } from 'react';
import Link from 'next/link';

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="dashboard-page">
      <div className="dashboard-container" style={{ textAlign: 'center', paddingTop: '80px' }}>
        <div className="dash-stat-card" style={{ maxWidth: '600px', margin: '0 auto' }}>
          <h2 className="dash-title" style={{ color: 'var(--color-fail)', marginBottom: '16px' }}>
            ไม่สามารถโหลดแดชบอร์ดได้
          </h2>
          <p className="dash-url" style={{ marginBottom: '24px' }}>
            {error.message || 'An unexpected error occurred while loading dashboard metrics.'}
          </p>
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
            <button className="scan-btn" onClick={() => reset()}>
              ลองใหม่อีกครั้ง
            </button>
            <Link href="/" className="dash-back-btn">
              ◄ กลับไปหน้าสแกน
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
