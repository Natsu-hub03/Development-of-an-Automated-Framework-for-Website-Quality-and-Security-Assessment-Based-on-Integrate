'use client';
import { useEffect } from 'react';
import Link from 'next/link';

export default function GlobalError({
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
    <div className="page-wrapper" style={{ justifyContent: 'center', alignItems: 'center' }}>
      <div className="scanner-card" style={{ textAlign: 'center' }}>
        <h2 className="dash-title" style={{ color: 'var(--color-fail)', marginBottom: '16px' }}>
          เกิดข้อผิดพลาดในการทำงาน
        </h2>
        <p className="dash-url" style={{ marginBottom: '24px' }}>
          {error.message || 'An unexpected error occurred while rendering the page.'}
        </p>
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
          <button className="scan-btn" onClick={() => reset()}>
            ลองใหม่อีกครั้ง
          </button>
          <Link href="/" className="dash-back-btn">
            กลับหน้าแรก
          </Link>
        </div>
      </div>
    </div>
  );
}
