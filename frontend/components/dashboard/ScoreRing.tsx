'use client';
import React from 'react';

interface ScoreRingProps {
  passRate: number;
  grade: {
    cls: string;
    label: string;
  };
}

export function ScoreRing({ passRate, grade }: ScoreRingProps) {
  return (
    <section className="dash-score-section fade-in-delay-1" aria-label="Overall Score">
      <div className="dash-score-ring-wrap">
        <div
          className="dash-score-ring"
          style={{ '--score-pct': passRate } as React.CSSProperties}
        />
        <div className="dash-score-inner">
          <div className="dash-score-value">
            {passRate}<span className="dash-score-unit">%</span>
          </div>
          <div className="dash-score-label">compliance</div>
          <div className={`dash-score-grade ${grade.cls}`}>
            {grade.label}
          </div>
        </div>
      </div>
    </section>
  );
}
