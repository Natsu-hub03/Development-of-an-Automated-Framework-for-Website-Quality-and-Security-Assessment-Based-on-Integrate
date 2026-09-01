'use client';
import React from 'react';
import { STANDARD_ICONS } from '../../lib/constants';
import type { StandardReport } from '../../lib/types';

interface StandardsGridProps {
  standards: StandardReport[];
  selectedStandard: string | null;
  onCardClick: (stdId: string) => void;
  onTagClick: (e: React.MouseEvent, stdId: string, status: 'pass' | 'fail' | 'warning') => void;
}

export function StandardsGrid({
  standards,
  selectedStandard,
  onCardClick,
  onTagClick,
}: StandardsGridProps) {
  return (
    <div className="dash-section">
      <div className="dash-section-title">// สรุปผลแยกตามแต่ละมาตรฐาน</div>
      <div className="dash-standards-grid">
        {standards.map((std) => {
          const stdPassRate = std.total > 0
            ? Math.round((std.passed / std.total) * 100)
            : 0;
          const isSelected = selectedStandard === std.id;

          return (
            <div
              key={std.id}
              className={`dash-std-card dash-std-card--clickable ${isSelected ? 'dash-std-card--active' : ''}`}
              onClick={() => onCardClick(std.id)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') onCardClick(std.id);
              }}
              aria-pressed={isSelected}
              title={isSelected ? 'คลิกเพื่อยกเลิกการกรอง' : `คลิกเพื่อกรองดูเฉพาะ ${std.name}`}
            >
              <div className="dash-std-header">
                <div className="dash-std-icon">
                  {STANDARD_ICONS[std.id] ?? '📋'}
                </div>
                <div className="dash-std-info">
                  <div className="dash-std-name">{std.name}</div>
                  <div className="dash-std-owner">{std.owner}</div>
                </div>
              </div>

              <div className="dash-gauge-wrap">
                <div
                  className="dash-gauge"
                  style={{ '--score-pct': stdPassRate } as React.CSSProperties}
                />
                <div className="dash-gauge-inner">
                  <div className="dash-gauge-value">
                    {stdPassRate}<span className="dash-gauge-unit">%</span>
                  </div>
                  <div className="dash-gauge-sub">{std.passed}/{std.total}</div>
                </div>
              </div>

              <div className="dash-std-counts">
                <button
                  type="button"
                  className="dash-std-count-tag dash-std-count-tag--pass"
                  onClick={(e) => onTagClick(e, std.id, 'pass')}
                  title={`ดูเฉพาะข้อที่ผ่านของ ${std.name}`}
                >
                  ✅ {std.passed} ผ่าน
                </button>
                <button
                  type="button"
                  className="dash-std-count-tag dash-std-count-tag--fail"
                  onClick={(e) => onTagClick(e, std.id, 'fail')}
                  title={`ดูเฉพาะข้อที่ไม่ผ่านของ ${std.name}`}
                >
                  ❌ {std.failed} ไม่ผ่าน
                </button>
                <button
                  type="button"
                  className="dash-std-count-tag dash-std-count-tag--warn"
                  onClick={(e) => onTagClick(e, std.id, 'warning')}
                  title={`ดูเฉพาะข้อที่เตือนของ ${std.name}`}
                >
                  ⚠️ {std.warning} เตือน
                </button>
              </div>

              <div className="dash-std-progress">
                <div
                  className="dash-std-progress-fill"
                  style={{ width: `${stdPassRate}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
