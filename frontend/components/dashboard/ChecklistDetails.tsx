'use client';
import React, { useState } from 'react';
import { STANDARD_ICONS, STATUS_CONFIG } from '../../lib/constants';
import type { StandardReport, CheckItem, CheckStatus, EvidenceNode } from '../../lib/types';

interface ChecklistDetailsProps {
  standards: StandardReport[];
  selectedStandard: string | null;
  onClearStandard: () => void;
  activeFilter: 'all' | 'pass' | 'fail' | 'warning';
  onFilterChange: (filter: 'all' | 'pass' | 'fail' | 'warning') => void;
  failedItems: CheckItem[];
  warningItems: CheckItem[];
  passedItems: CheckItem[];
}

export function ChecklistDetails({
  standards,
  selectedStandard,
  onClearStandard,
  activeFilter,
  onFilterChange,
  failedItems,
  warningItems,
  passedItems,
}: ChecklistDetailsProps) {
  const [expandedEvidence, setExpandedEvidence] = useState<Set<string>>(new Set());

  const toggleEvidence = (key: string) => {
    setExpandedEvidence((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  // Filter items by selected standard if active
  const stdFilteredFailed = selectedStandard
    ? failedItems.filter((it) => it.standardId === selectedStandard)
    : failedItems;
  const stdFilteredWarning = selectedStandard
    ? warningItems.filter((it) => it.standardId === selectedStandard)
    : warningItems;
  const stdFilteredPassed = selectedStandard
    ? passedItems.filter((it) => it.standardId === selectedStandard)
    : passedItems;

  const allItems = [...stdFilteredFailed, ...stdFilteredWarning, ...stdFilteredPassed];
  const filteredItems =
    activeFilter === 'all'
      ? allItems
      : activeFilter === 'pass'
        ? stdFilteredPassed
        : activeFilter === 'fail'
          ? stdFilteredFailed
          : stdFilteredWarning;

  const activeStdObj = selectedStandard
    ? standards.find((s) => s.id === selectedStandard)
    : null;

  return (
    <div className="dash-section" id="checklist-details-section">
      <div className="dash-section-header-row">
        <div className="dash-section-title">// รายละเอียดรายการตรวจสอบทั้งหมด</div>
        {activeStdObj && (
          <div className="dash-active-std-pill">
            <span>
              กำลังกรอง: <strong>{STANDARD_ICONS[activeStdObj.id]} {activeStdObj.name}</strong>
            </span>
            <button
              className="dash-clear-std-btn"
              onClick={onClearStandard}
              title="ล้างตัวกรองมาตรฐานเพื่อดูทั้งหมด 68 ข้อ"
            >
              ✕ ดูทั้งหมด 68 ข้อ
            </button>
          </div>
        )}
      </div>

      <div className="dash-filter-tabs">
        <button
          className={`dash-filter-tab ${activeFilter === 'all' ? 'dash-filter-tab--active' : ''}`}
          onClick={() => onFilterChange('all')}
        >
          📋 ทั้งหมด <span className="dash-filter-tab-count">{allItems.length}</span>
        </button>
        <button
          className={`dash-filter-tab dash-filter-tab--fail ${activeFilter === 'fail' ? 'dash-filter-tab--active' : ''}`}
          onClick={() => onFilterChange('fail')}
        >
          ❌ ไม่ผ่าน <span className="dash-filter-tab-count">{stdFilteredFailed.length}</span>
        </button>
        <button
          className={`dash-filter-tab dash-filter-tab--warn ${activeFilter === 'warning' ? 'dash-filter-tab--active' : ''}`}
          onClick={() => onFilterChange('warning')}
        >
          ⚠️ เตือน <span className="dash-filter-tab-count">{stdFilteredWarning.length}</span>
        </button>
        <button
          className={`dash-filter-tab dash-filter-tab--pass ${activeFilter === 'pass' ? 'dash-filter-tab--active' : ''}`}
          onClick={() => onFilterChange('pass')}
        >
          ✅ ผ่าน <span className="dash-filter-tab-count">{stdFilteredPassed.length}</span>
        </button>
      </div>

      <div className="dash-checklist-wrap">
        {filteredItems.length > 0 ? (
          <div className="dash-checklist-list">
            {filteredItems.map((item, i) => {
              const evKey = `${item.id}-${i}`;
              const isEvidenceOpen = expandedEvidence.has(evKey);
              const hasEvidence = item.evidence && item.evidence.length > 0;
              const isPass = item.status === 'pass';
              const cfg = STATUS_CONFIG[item.status as CheckStatus] ?? STATUS_CONFIG.warning;

              return (
                <div
                  key={evKey}
                  className={`dash-checklist-item dash-checklist-item--${item.status} ${isPass ? 'dash-checklist-item--compact' : ''}`}
                >
                  <div className="dash-checklist-item-main">
                    <span className="dash-checklist-status-icon">
                      {cfg.icon}
                    </span>
                    {item.standardId && (
                      <span className="dash-failed-std-badge">
                        {STANDARD_ICONS[item.standardId]} {item.standardId}
                      </span>
                    )}

                    <div className="dash-failed-info">
                      <div className="dash-failed-header-row">
                        <div className="dash-failed-name">
                          {item.name}
                          {item.name_th && (
                            <span className="dash-failed-name-th"> ({item.name_th})</span>
                          )}
                          <span className="dash-item-id-pill">{item.id}</span>
                        </div>

                        {/* Evidence button in header for compact scanning */}
                        {hasEvidence && (
                          <button
                            className={`dash-evidence-toggle ${isEvidenceOpen ? 'dash-evidence-toggle--open' : ''}`}
                            onClick={() => toggleEvidence(evKey)}
                            aria-label="ดูตำแหน่งโค้ดและหลักฐาน"
                            title="ดูตำแหน่งโค้ด & Selector"
                          >
                            📍 <span>{isPass ? 'โค้ดที่ผ่าน' : 'จุดที่พบ'} ({item.evidence?.length})</span>
                            <span className={`dash-evidence-arrow ${isEvidenceOpen ? 'rotated' : ''}`}>▼</span>
                          </button>
                        )}
                      </div>

                      {/* Concise Result Line */}
                      {item.detail && (
                        <div className="dash-failed-detail">
                          <span className="dash-detail-tag">{isPass ? 'ผลการตรวจ:' : 'ปัญหาที่พบ:'}</span> {item.detail}
                        </div>
                      )}

                      {/* ⚡ ความเสี่ยง (แสดงข้อมูลมาตรฐานทันที) */}
                      {!isPass && item.why_th && (
                        <div className="dash-risk-box">
                          <span className="dash-risk-box-icon">⚡</span>
                          <span className="dash-risk-box-text">
                            <strong>ความเสี่ยง:</strong> {item.why_th}
                          </span>
                        </div>
                      )}

                      {/* 💡 วิธีแก้ไข (แสดงคำแนะนำมาตรฐานทันที) */}
                      {!isPass && item.remediation_th && (
                        <div className="dash-fix-box">
                          <span className="dash-fix-icon">💡</span>
                          <span className="dash-fix-text">
                            <strong>วิธีแก้:</strong> {item.remediation_th}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* 📍 Evidence Panel (Pass / Fail / Warn) */}
                  {hasEvidence && isEvidenceOpen && item.evidence && (
                    <div className="dash-evidence-panel">
                      <div className="dash-evidence-title">
                        📍 {isPass ? 'หลักฐาน/โค้ดที่ตรวจสอบผ่าน' : 'ตำแหน่งโค้ดและรายละเอียด'}
                      </div>
                      {item.evidence.map((ev: EvidenceNode, ei: number) => (
                        <div key={ei} className="dash-evidence-node">
                          {ev.target && ev.target.length > 0 && (
                            <div className="dash-evidence-selector">
                              <span className="dash-evidence-label">ตำแหน่ง:</span>
                              <code className="dash-evidence-code">
                                {Array.isArray(ev.target) ? ev.target.join(' > ') : ev.target}
                              </code>
                            </div>
                          )}
                          {ev.html && (
                            <div className="dash-evidence-html">
                              <span className="dash-evidence-label">โค้ด:</span>
                              <pre className="dash-evidence-pre"><code>{ev.html}</code></pre>
                            </div>
                          )}
                          {(ev.failureSummary || ev.passed_summary || ev.summary) && (
                            <div className="dash-evidence-summary">
                              <span className="dash-evidence-label">รายละเอียด:</span>
                              <span className="dash-evidence-reason">
                                {ev.failureSummary || ev.passed_summary || ev.summary}
                              </span>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="dash-failed-none">ไม่พบรายการในหมวดนี้</div>
        )}
      </div>
    </div>
  );
}
