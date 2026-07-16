'use client';
import { useState } from 'react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

type ScanType = 'wappalyzer' | 'zap' | 'both';

export default function Home() {
  const [url, setUrl] = useState('');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [scanStatus, setScanStatus] = useState<'idle' | 'scanning' | 'done' | 'error'>('idle');
  const [scanType, setScanType] = useState<ScanType>('both');

  const runScan = async (type: 'wappalyzer' | 'zap') => {
    const res = await fetch(`${API_BASE_URL}/scan/${type}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    });
    return res.json();
  };

  const handleScan = async () => {
    if (!url) return;
    setLoading(true);
    setResult(null);
    setScanStatus('scanning');
    try {
      let data: any;
      if (scanType === 'both') {
        const [wapResult, zapResult] = await Promise.all([
          runScan('wappalyzer'),
          runScan('zap'),
        ]);
        data = { wappalyzer: wapResult, zap: zapResult };
      } else {
        data = await runScan(scanType);
      }
      setResult(data);
      setScanStatus('done');
    } catch (err) {
      console.error(err);
      setResult({ error: 'ไม่สามารถเชื่อมต่อกับ Backend ได้ กรุณาตรวจสอบว่า Server กำลังทำงานอยู่' });
      setScanStatus('error');
    }
    setLoading(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && url && !loading) {
      handleScan();
    }
  };

  const getStatusText = () => {
    switch (scanStatus) {
      case 'idle': return 'พร้อมสแกน';
      case 'scanning': return 'กำลังสแกน...';
      case 'done': return 'สแกนเสร็จสิ้น';
      case 'error': return 'เกิดข้อผิดพลาด';
    }
  };

  const getStatusClass = () => {
    switch (scanStatus) {
      case 'idle': return '';
      case 'scanning': return 'scanning';
      case 'done': return 'ready';
      case 'error': return 'error';
    }
  };

  const resultCount = result && !result.error
    ? (Array.isArray(result) ? result.length : Object.keys(result).length)
    : 0;

  return (
    <>
      {/* Background Orbs */}
      <div className="bg-orbs" aria-hidden="true" />

      <div className="page-wrapper">
        {/* Navbar */}
        <nav className="navbar fade-in" role="navigation" aria-label="Main navigation">
          <a href="/" className="navbar-brand" id="nav-home-link">
            <div className="navbar-logo" aria-hidden="true">W</div>
            <span className="navbar-title">WebScan</span>
          </a>
          <span className="navbar-badge">v1.0</span>
        </nav>

        {/* Hero Section */}
        <section className="hero-section fade-in-delay-1">
          <h1 className="hero-title" id="hero-heading">
            Web Standards Scanner
          </h1>
          <p className="hero-subtitle">
            วิเคราะห์เทคโนโลยีและมาตรฐานเว็บไซต์ของคุณอย่างรวดเร็ว ปลอดภัย และแม่นยำ
          </p>
        </section>

        {/* Scanner Card */}
        <section className="scanner-card fade-in-delay-2" aria-label="URL Scanner">
          <label htmlFor="url-input" className="scanner-label">
            กรอก URL ที่ต้องการสแกน
          </label>

          {/* Scan Type Selector */}
          <div className="scan-type-selector" id="scan-type-selector">
            {(['wappalyzer', 'zap', 'both'] as ScanType[]).map((type) => (
              <button
                key={type}
                className={`scan-type-btn ${scanType === type ? 'active' : ''}`}
                onClick={() => setScanType(type)}
                disabled={loading}
              >
                {type === 'wappalyzer' && '🛠️ Wappalyzer'}
                {type === 'zap' && '⚡ ZAP Scan'}
                {type === 'both' && '🔍 ทั้งหมด'}
              </button>
            ))}
          </div>

          <div className="input-group">
            <input
              id="url-input"
              type="url"
              className="url-input"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="https://example.com"
              aria-label="URL ที่ต้องการสแกน"
              autoComplete="url"
              spellCheck={false}
            />
            <button
              id="scan-button"
              className="scan-btn"
              onClick={handleScan}
              disabled={loading || !url}
              aria-label={loading ? 'กำลังสแกน' : 'เริ่มสแกน'}
            >
              {loading && <span className="spinner" aria-hidden="true" />}
              {loading ? 'กำลังสแกน...' : '🔍 สแกน'}
            </button>
          </div>

          {/* Status Indicator */}
          <div className="scan-status" aria-live="polite">
            <span className={`status-dot ${getStatusClass()}`} aria-hidden="true" />
            <span>{getStatusText()}</span>
          </div>

          {/* Error Banner */}
          {result?.error && (
            <div className="error-banner" role="alert" id="error-message">
              <span className="error-icon" aria-hidden="true">⚠️</span>
              <span>{result.error}</span>
            </div>
          )}

          {/* Results */}
          {result && !result.error && (
            <div className="results-wrapper" id="scan-results">
              <div className="results-header">
                <span className="results-title">ผลการสแกน</span>
                {resultCount > 0 && (
                  <span className="results-count">
                    {resultCount} รายการ
                  </span>
                )}
              </div>
              <pre className="results-code" tabIndex={0} aria-label="ผลลัพธ์การสแกน">
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          )}
        </section>

        {/* Features Section */}
        <section className="features-section fade-in-delay-3" aria-label="Features">
          <div className="features-grid">
            <div className="feature-card" id="feature-tech">
              <span className="feature-icon" aria-hidden="true">🛠️</span>
              <h3 className="feature-title">ตรวจจับเทคโนโลยี</h3>
              <p className="feature-desc">
                วิเคราะห์ Framework, CMS, Library และเทคโนโลยีที่เว็บไซต์ใช้งาน
              </p>
            </div>
            <div className="feature-card" id="feature-security">
              <span className="feature-icon" aria-hidden="true">🔒</span>
              <h3 className="feature-title">ตรวจสอบความปลอดภัย</h3>
              <p className="feature-desc">
                ตรวจหาช่องโหว่และจุดอ่อนด้านความปลอดภัยของเว็บไซต์
              </p>
            </div>
            <div className="feature-card" id="feature-standards">
              <span className="feature-icon" aria-hidden="true">📋</span>
              <h3 className="feature-title">มาตรฐานเว็บ</h3>
              <p className="feature-desc">
                ประเมินการปฏิบัติตามมาตรฐาน W3C, WCAG และ Best Practices
              </p>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="footer" id="site-footer">
          <p>
            © 2026 WebScan — เครื่องมือวิเคราะห์มาตรฐานเว็บไซต์ ·{' '}
            <a href="https://github.com" target="_blank" rel="noopener noreferrer">
              GitHub
            </a>
          </p>
        </footer>
      </div>
    </>
  );
}