'use client';
import { useState, useCallback } from 'react';
import type { ScanApiResponse } from '../lib/types';
import { executeAiAnalysis } from '../lib/api';

interface UseAiAnalysisReturn {
  aiResult: string | null;
  aiModel: string;
  aiLoading: boolean;
  aiError: string | null;
  handleAiAnalyze: () => Promise<void>;
  clearAiState: () => void;
}

interface UseAiAnalysisOptions {
  url: string;
  lastScannedUrl: string;
  result: ScanApiResponse | null;
  scanType: string;
  resultsByType: Record<string, unknown>;
}

export function useAiAnalysis({
  url,
  lastScannedUrl,
  result,
  scanType,
  resultsByType,
}: UseAiAnalysisOptions): UseAiAnalysisReturn {
  const [aiResult, setAiResult]   = useState<string | null>(null);
  const [aiModel, setAiModel]     = useState<string>('qwen2.5:3b');
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError]     = useState<string | null>(null);

  const clearAiState = useCallback(() => {
    setAiResult(null);
    setAiError(null);
  }, []);

  const handleAiAnalyze = useCallback(async () => {
    if (!result || !url) return;
    setAiLoading(true);
    setAiError(null);
    setAiResult(null);
    try {
      const data: ScanApiResponse = await executeAiAnalysis(url, result, scanType);
      if (!data || data.error || !data.success) {
        setAiError(data.error || 'AI analysis failed');
      } else {
        const text = data.analysis || '';
        const model = data.model || 'qwen2.5:3b';
        setAiResult(text);
        setAiModel(model);
        try {
          localStorage.setItem(
            'webscan_state',
            JSON.stringify({
              url: url.trim(),
              lastScannedUrl: lastScannedUrl || url.trim(),
              scanType,
              resultsByType,
              result,
              aiResult: text,
              aiModel: model,
            })
          );
        } catch { /* ignore */ }
      }
    } catch {
      setAiError('ไม่สามารถเชื่อมต่อกับ AI service ได้');
    }
    setAiLoading(false);
  }, [url, lastScannedUrl, result, scanType, resultsByType]);

  return {
    aiResult,
    aiModel,
    aiLoading,
    aiError,
    handleAiAnalyze,
    clearAiState,
  };
}
