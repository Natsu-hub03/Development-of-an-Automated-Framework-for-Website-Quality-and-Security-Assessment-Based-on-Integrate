'use client';
import React from 'react';
import type { Technology } from '../../lib/types';

interface TechStackGridProps {
  technologies: Technology[];
}

export function TechStackGrid({ technologies }: TechStackGridProps) {
  if (!technologies || technologies.length === 0) return null;

  return (
    <div className="dash-section">
      <div className="dash-section-title">
        // 🛠 เทคโนโลยีและไลบรารีที่ตรวจพบ ({technologies.length})
      </div>
      <div className="dash-tech-grid">
        {technologies.map((tech, i) => {
          const iconUrl = tech.icon
            ? `https://www.wappalyzer.com/images/icons/${tech.icon}`
            : null;

          return (
            <div key={i} className="dash-tech-card">
              <div className="dash-tech-icon-box">
                {iconUrl ? (
                  <img
                    src={iconUrl}
                    alt={tech.name}
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = 'none';
                      const parent = (e.target as HTMLElement).parentElement;
                      const fallback = parent?.querySelector('.dash-tech-fallback-letter');
                      if (fallback) (fallback as HTMLElement).style.display = 'flex';
                    }}
                  />
                ) : null}
                <span
                  className="dash-tech-fallback-letter"
                  style={{ display: iconUrl ? 'none' : 'flex' }}
                >
                  {(tech.name || '?')[0].toUpperCase()}
                </span>
              </div>
              <div className="dash-tech-info">
                <div className="dash-tech-name">
                  {tech.name}
                  {tech.version && (
                    <span className="dash-tech-version"> {tech.version}</span>
                  )}
                </div>
                <div className="dash-tech-cat">
                  {(tech.categories || []).map((c) => c.name).join(', ') || 'Other'}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
