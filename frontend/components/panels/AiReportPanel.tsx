'use client';
import React from 'react';

interface AiReportPanelProps {
  url: string;
  analysis: string;
  model?: string;
}

/**
 * Safely parse bold markers (**text**) and inline code (`code`) into React elements without dangerouslySetInnerHTML.
 * This completely eliminates XSS vulnerabilities.
 */
function renderInlineFormatted(text: string): React.ReactNode {
  const parts = text.split(/(\*\*.*?\*\*|`.*?`)/g);
  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return <code key={index} className="ai-inline-code">{part.slice(1, -1)}</code>;
    }
    return part;
  });
}

export function AiReportPanel({ url, analysis, model }: AiReportPanelProps) {
  const rawLines = analysis.split('\n');

  // Process lines into structured blocks (handling code fences)
  const renderedElements: React.ReactNode[] = [];
  let inCodeBlock = false;
  let codeBuffer: string[] = [];

  for (let i = 0; i < rawLines.length; i++) {
    const line = rawLines[i];
    const trimmed = line.trim();

    if (trimmed.startsWith('```')) {
      if (inCodeBlock) {
        renderedElements.push(
          <pre key={`code-${i}`} className="ai-code-block">
            <code>{codeBuffer.join('\n')}</code>
          </pre>
        );
        codeBuffer = [];
        inCodeBlock = false;
      } else {
        inCodeBlock = true;
      }
      continue;
    }

    if (inCodeBlock) {
      codeBuffer.push(line);
      continue;
    }

    if (line.startsWith('## ')) {
      renderedElements.push(<h3 key={i} className="ai-heading-2">{line.slice(3)}</h3>);
    } else if (line.startsWith('### ')) {
      renderedElements.push(<h4 key={i} className="ai-heading-3">{line.slice(4)}</h4>);
    } else if (line.startsWith('- ') || line.startsWith('• ') || line.startsWith('* ')) {
      const content = line.startsWith('• ') ? line.slice(2) : line.slice(2);
      renderedElements.push(
        <li key={i} className="ai-list-item">
          {renderInlineFormatted(content)}
        </li>
      );
    } else if (/^\d+\.\s/.test(trimmed)) {
      renderedElements.push(
        <div key={i} className="ai-num-item">
          {renderInlineFormatted(line)}
        </div>
      );
    } else if (trimmed === '') {
      renderedElements.push(<div key={i} className="ai-spacer" />);
    } else {
      renderedElements.push(
        <p key={i} className="ai-para">
          {renderInlineFormatted(line)}
        </p>
      );
    }
  }

  // If code fence was not closed
  if (inCodeBlock && codeBuffer.length > 0) {
    renderedElements.push(
      <pre key="code-unclosed" className="ai-code-block">
        <code>{codeBuffer.join('\n')}</code>
      </pre>
    );
  }

  return (
    <div className="ai-panel" id="ai-report" aria-label="AI Security Analysis">
      <div className="ai-panel-header">
        <div className="ai-panel-header-left">
          <span className="ai-panel-title">// AI SECURITY & COMPLIANCE REPORT</span>
          {model && <span className="ai-model-badge">{model} · Ollama</span>}
        </div>
        <span className="ai-panel-url">{url}</span>
      </div>
      <div className="ai-panel-body">
        {renderedElements}
      </div>
    </div>
  );
}
