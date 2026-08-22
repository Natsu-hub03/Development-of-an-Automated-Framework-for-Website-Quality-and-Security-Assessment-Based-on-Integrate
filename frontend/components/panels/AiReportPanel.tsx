'use client';
import React from 'react';

interface AiReportPanelProps {
  url: string;
  analysis: string;
  model?: string;
}

/**
 * Safely parse bold markers (**text**) into React elements without using dangerouslySetInnerHTML.
 * This completely eliminates XSS vulnerabilities.
 */
function renderInlineFormatted(text: string): React.ReactNode {
  const parts = text.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }
    return part;
  });
}

export function AiReportPanel({ url, analysis, model }: AiReportPanelProps) {
  const lines = analysis.split('\n');

  return (
    <div className="ai-panel" id="ai-report" aria-label="AI Security Analysis">
      <div className="ai-panel-header">
        <div className="ai-panel-header-left">
          <span className="ai-panel-title">// AI SECURITY REPORT</span>
          {model && <span className="ai-model-badge">{model} · Ollama</span>}
        </div>
        <span className="ai-panel-url">{url}</span>
      </div>
      <div className="ai-panel-body">
        {lines.map((line, i) => {
          const trimmed = line.trim();
          if (line.startsWith('## ')) {
            return <h3 key={i} className="ai-heading-2">{line.slice(3)}</h3>;
          }
          if (line.startsWith('### ')) {
            return <h4 key={i} className="ai-heading-3">{line.slice(4)}</h4>;
          }
          if (line.startsWith('- ')) {
            return (
              <li key={i} className="ai-list-item">
                {renderInlineFormatted(line.slice(2))}
              </li>
            );
          }
          if (trimmed === '') {
            return <div key={i} className="ai-spacer" />;
          }
          return (
            <p key={i} className="ai-para">
              {renderInlineFormatted(line)}
            </p>
          );
        })}
      </div>
    </div>
  );
}
