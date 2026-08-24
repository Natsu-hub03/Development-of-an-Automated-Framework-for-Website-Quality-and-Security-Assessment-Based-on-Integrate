'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getGrade } from '../../lib/constants';
import type { StandardsReportData, ScanApiResponse, ScanResultsMap } from '../../lib/types';
import { extractChecks, combineScanResults } from '../../lib/utils';
import { ScoreRing } from '../../components/dashboard/ScoreRing';
import { StandardsGrid } from '../../components/dashboard/StandardsGrid';
import { ChecklistDetails } from '../../components/dashboard/ChecklistDetails';
import { TechStackGrid } from '../../components/dashboard/TechStackGrid';

export default function DashboardPage() {
  const [data, setData] = useState<StandardsReportData | null>(null);
  const [mounted, setMounted] = useState(false);
  const [selectedStandard, setSelectedStandard] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<'all' | 'pass' | 'fail' | 'warning'>('all');

  const handleCardClick = (stdId: string) => {
    setSelectedStandard((prev) => (prev === stdId ? null : stdId));
    const el = document.getElementById('checklist-details-section');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const handleTagClick = (e: React.MouseEvent, stdId: string, status: 'pass' | 'fail' | 'warning') => {
    e.stopPropagation();
    setSelectedStandard(stdId);
    setActiveFilter(status);
    const el = document.getElementById('checklist-details-section');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  useEffect(() => {
    setMounted(true);
    try {
      const rawMap = localStorage.getItem('webscan_results_by_type');
      const rawDashboard = localStorage.getItem('webscan_dashboard_data');

      const map: ScanResultsMap = rawMap ? JSON.parse(rawMap) : {};
      const dashboardData: ScanApiResponse | null = rawDashboard ? JSON.parse(rawDashboard) : null;

      const combined = combineScanResults(map, dashboardData);
      if (combined) {
        setData(combined);
      }
    } catch {
      // ignore parse errors
    }
  }, []);

  if (!mounted) return null;

  // Empty state
  if (!data) {
    return (
      <>
        <div className="crt-overlay" aria-hidden="true" />
        <div className="bg-orbs" aria-hidden="true" />
        <div className="dashboard-page">
          <nav className="navbar" role="navigation" aria-label="Main navigation">
            <Link href="/" className="navbar-brand">
              <div className="navbar-logo" aria-hidden="true">W</div>
              <span className="navbar-title">WebScan</span>
            </Link>
          </nav>
          <div className="dashboard-container">
            <div className="dash-empty">
              <div className="dash-empty-icon">📊</div>
              <div className="dash-empty-text">
                ยังไม่มีผลการสแกน กรุณาสแกนเว็บไซต์ก่อน
              </div>
              <Link href="/" className="dash-empty-btn">
                ◄ กลับไปสแกน
              </Link>
            </div>
          </div>
        </div>
      </>
    );
  }

  const summary = data.summary ?? { total: 0, passed: 0, failed: 0, warning: 0 };
  const standards = data.standards ?? [];
  const technologies = data.wappalyzer_technologies ?? [];
  const url = data.url ?? '';
  const timestamp = data.timestamp ?? '';

  const totalChecks = summary.total || 1;
  const passRate = Math.round((summary.passed / totalChecks) * 100);
  const failRate = Math.round((summary.failed / totalChecks) * 100);
  const warnRate = Math.round((summary.warning / totalChecks) * 100);
  const grade = getGrade(passRate);

  const failedItems = extractChecks(standards, 'fail');
  const warningItems = extractChecks(standards, 'warning');
  const passedItems = extractChecks(standards, 'pass');

  const formattedTime = timestamp
    ? new Date(timestamp).toLocaleString('th-TH', {
        year: 'numeric', month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit',
      })
    : '';

  return (
    <>
      <div className="crt-overlay" aria-hidden="true" />
      <div className="bg-orbs" aria-hidden="true" />

      <div className="dashboard-page">
        {/* Navbar */}
        <nav className="navbar fade-in" role="navigation" aria-label="Dashboard navigation">
          <Link href="/" className="navbar-brand" id="nav-home-link">
            <div className="navbar-logo" aria-hidden="true">W</div>
            <span className="navbar-title">WebScan</span>
          </Link>
          <div className="navbar-right">
            <div className="navbar-status-dot" aria-hidden="true" />
            <span>DASHBOARD</span>
            <span className="navbar-badge">v1.0</span>
          </div>
        </nav>

        <div className="dashboard-container">
          {/* Header */}
          <header className="dash-header fade-in">
            <div className="dash-header-left">
              <h1 className="dash-title">
                Scan <span className="dash-title-accent">Dashboard</span>
              </h1>
              {url && <div className="dash-url">{url}</div>}
              {formattedTime && <div className="dash-timestamp">🕐 {formattedTime}</div>}
            </div>
            <div className="dash-actions">
              <button
                className="dash-action-btn"
                onClick={() => window.print()}
                aria-label="พิมพ์รายงาน"
              >
                🖨️ PRINT
              </button>
              <Link href="/" className="dash-back-btn">
                ◄ BACK TO SCANNER
              </Link>
            </div>
          </header>

          {/* Overall Score Ring */}
          <ScoreRing passRate={passRate} grade={grade} />

          {/* Summary Stats */}
          <div className="dash-stats-grid" role="group" aria-label="Summary Statistics">
            <div className="dash-stat-card dash-stat-card--total">
              <div className="dash-stat-icon">📋</div>
              <div className="dash-stat-value">{summary.total}</div>
              <div className="dash-stat-label">รายการทั้งหมด</div>
              <div className="dash-stat-sub">{standards.length} มาตรฐาน</div>
            </div>
            <div className="dash-stat-card dash-stat-card--pass">
              <div className="dash-stat-icon">✅</div>
              <div className="dash-stat-value">{summary.passed}</div>
              <div className="dash-stat-label">ผ่าน</div>
              <div className="dash-stat-sub">{passRate}%</div>
            </div>
            <div className="dash-stat-card dash-stat-card--fail">
              <div className="dash-stat-icon">❌</div>
              <div className="dash-stat-value">{summary.failed}</div>
              <div className="dash-stat-label">ไม่ผ่าน</div>
              <div className="dash-stat-sub">{failRate}%</div>
            </div>
            <div className="dash-stat-card dash-stat-card--warn">
              <div className="dash-stat-icon">⚠️</div>
              <div className="dash-stat-value">{summary.warning}</div>
              <div className="dash-stat-label">เตือน</div>
              <div className="dash-stat-sub">{warnRate}%</div>
            </div>
          </div>

          {/* Per-Standard Gauge Cards */}
          <StandardsGrid
            standards={standards}
            selectedStandard={selectedStandard}
            onCardClick={handleCardClick}
            onTagClick={handleTagClick}
          />

          {/* Checklist Details */}
          <ChecklistDetails
            standards={standards}
            selectedStandard={selectedStandard}
            onClearStandard={() => setSelectedStandard(null)}
            activeFilter={activeFilter}
            onFilterChange={setActiveFilter}
            failedItems={failedItems}
            warningItems={warningItems}
            passedItems={passedItems}
          />

          {/* Tech Stack */}
          <TechStackGrid technologies={technologies} />

          {/* Footer */}
          <footer className="footer" id="site-footer">
            <p>
              © 2026 WebScan &mdash; AI-Assisted Web Standards &amp; Vulnerability Assessment
            </p>
          </footer>
        </div>
      </div>
    </>
  );
}
