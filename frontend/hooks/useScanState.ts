'use client';
import { useState, useEffect, useCallback } from 'react';
import type { ScanType, ScanStatus, ScanResultsMap, ScanApiResponse, StandardReport } from '../lib/types';
import { executeScan } from '../lib/api';
import { normalizeUrl, unwrapReportData, extractChecks } from '../lib/utils';

interface UseScanStateReturn {
  url: string;
  setUrl: (url: string) => void;
  lastScannedUrl: string;
  result: ScanApiResponse | null;
  loading: boolean;
  scanStatus: ScanStatus;
  scanType: ScanType;
  resultsByType: ScanResultsMap;
  expandedMap: Record<string, boolean>;
  setExpandedMap: React.Dispatch<React.SetStateAction<Record<string, boolean>>>;
  handleSelectScanType: (type: ScanType) => void;
  handleScan: () => Promise<void>;
  handleReset: () => void;
  handleKeyDown: (e: React.KeyboardEvent) => void;
  getStatusText: () => string;
  getStatusClass: () => string;
  showResult: boolean;
  aiBatchReady: boolean;
}

export function useScanState(): UseScanStateReturn {
  const [url, setUrl]                       = useState('');
  const [lastScannedUrl, setLastScannedUrl] = useState('');
  const [result, setResult]                 = useState<ScanApiResponse | null>(null);
  const [loading, setLoading]               = useState(false);
  const [scanStatus, setScanStatus]         = useState<ScanStatus>('idle');
  const [scanType, setScanType]             = useState<ScanType>('standards');
  const [resultsByType, setResultsByType]   = useState<ScanResultsMap>({});
  const [expandedMap, setExpandedMap]       = useState<Record<string, boolean>>({});
  const [aiBatchReady, setAiBatchReady]     = useState(false);

  // Restore state from localStorage on mount
  useEffect(() => {
    try {
      const savedMap = localStorage.getItem('webscan_results_by_type');
      let map: ScanResultsMap = {};
      if (savedMap) {
        map = JSON.parse(savedMap);
        setResultsByType(map);
      }

      const saved = localStorage.getItem('webscan_state');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.url) {
          setUrl(parsed.url);
          setLastScannedUrl(parsed.lastScannedUrl || parsed.url);
        }
        const activeType = (parsed.scanType as ScanType) || 'standards';
        setScanType(activeType);

        if (parsed.resultsByType) {
          map = { ...map, ...parsed.resultsByType };
          setResultsByType(map);
        }

        const res = map[activeType] || parsed.result;
        if (res) {
          setResult(res);
          setScanStatus('done');
        }
      } else {
        const legacyData = localStorage.getItem('webscan_dashboard_data');
        if (legacyData) {
          const parsed = JSON.parse(legacyData);
          setResult(parsed);
          setScanStatus('done');
          const targetUrl = parsed.url || parsed.data?.url || '';
          if (targetUrl) {
            setUrl(targetUrl);
            setLastScannedUrl(targetUrl);
          }
        }
      }

      // Check if AI batch cache exists for restored state
      const cachedAi = localStorage.getItem('webscan_ai_batch_cache');
      if (cachedAi) {
        try {
          const parsed = JSON.parse(cachedAi);
          if (parsed.results && Object.keys(parsed.results).length > 0) {
            setAiBatchReady(true);
          }
        } catch { /* ignore */ }
      }
    } catch {
      // ignore parse errors
    }
  }, []);

  const handleSelectScanType = useCallback((type: ScanType) => {
    setScanType(type);
    let existing = resultsByType[type];

    // If sub-standard not yet explicitly stored, extract from all-standards result
    if (!existing && resultsByType['standards']) {
      const stdData = unwrapReportData(resultsByType['standards']);
      const std = stdData?.standards?.find((s: StandardReport) => s.id === type);
      if (std && stdData) {
        existing = {
          success: true,
          data: {
            url: stdData.url || url,
            timestamp: stdData.timestamp,
            summary: {
              total: std.total,
              passed: std.passed,
              failed: std.failed,
              warning: std.warning,
            },
            standards: [std],
            wappalyzer_technologies: stdData.wappalyzer_technologies,
          },
        };
      }
    }

    if (existing) {
      setResult(existing);
      setScanStatus('done');
    } else {
      setResult(null);
      setScanStatus('idle');
    }
  }, [resultsByType, url]);

  const handleScan = useCallback(async () => {
    const trimmedUrl = url.trim();
    if (!trimmedUrl) return;

    const normNew = normalizeUrl(trimmedUrl);
    const normOld = normalizeUrl(lastScannedUrl || '');
    const isNewUrl = !normOld || normNew !== normOld;

    setLoading(true);
    setResult(null);
    setScanStatus('scanning');
    setAiBatchReady(false);

    let baseMap: ScanResultsMap = {};
    if (isNewUrl) {
      setResultsByType({});
      setExpandedMap({});
      setLastScannedUrl(trimmedUrl);
      try {
        localStorage.removeItem('webscan_results_by_type');
        localStorage.removeItem('webscan_dashboard_data');
        localStorage.removeItem('webscan_state');
        localStorage.removeItem('webscan_ai_batch_cache');
      } catch { /* ignore */ }
    } else {
      baseMap = { ...resultsByType };
    }

    try {
      const data = await executeScan(scanType, trimmedUrl);
      if (data?.error) {
        setResult(data);
        setScanStatus('error');
        setLoading(false);
        return;
      }

      setResult(data);
      setLastScannedUrl(trimmedUrl);

      const updatedMap: ScanResultsMap = {
        ...baseMap,
        [scanType]: data,
      };

      // If all standards were scanned, populate individual sub-standards
      if (scanType === 'standards' && data) {
        const reportData = unwrapReportData(data);
        if (reportData?.standards) {
          for (const std of reportData.standards) {
            if (std?.id) {
              const stdId = std.id as ScanType;
              updatedMap[stdId] = {
                success: true,
                scan_id: data.scan_id,
                data: {
                  url: reportData.url || trimmedUrl,
                  timestamp: reportData.timestamp,
                  summary: {
                    total: std.total,
                    passed: std.passed,
                    failed: std.failed,
                    warning: std.warning,
                  },
                  standards: [std],
                  wappalyzer_technologies: reportData.wappalyzer_technologies,
                },
              };
            }
          }
        }
      }

      setResultsByType(updatedMap);

      try {
        localStorage.setItem('webscan_results_by_type', JSON.stringify(updatedMap));
        localStorage.setItem('webscan_dashboard_data', JSON.stringify(data));
        localStorage.setItem(
          'webscan_state',
          JSON.stringify({
            url: trimmedUrl,
            lastScannedUrl: trimmedUrl,
            scanType,
            resultsByType: updatedMap,
            result: data,
            aiResult: null,
            aiModel: 'qwen2.5:3b',
          })
        );
      } catch { /* ignore quota errors */ }

      setAiBatchReady(true);
      setScanStatus('done');
    } catch (err) {
      console.error(err);
      setResult({ error: 'ไม่สามารถเชื่อมต่อกับ Backend ได้ กรุณาตรวจสอบว่า Server กำลังทำงานอยู่' });
      setScanStatus('error');
    }
    setLoading(false);
  }, [url, lastScannedUrl, scanType, resultsByType]);

  const handleReset = useCallback(() => {
    setUrl('');
    setLastScannedUrl('');
    setResult(null);
    setScanStatus('idle');
    setResultsByType({});
    setExpandedMap({});
    try {
      localStorage.removeItem('webscan_state');
      localStorage.removeItem('webscan_dashboard_data');
      localStorage.removeItem('webscan_results_by_type');
      localStorage.removeItem('webscan_ai_batch_cache');
    } catch { /* ignore */ }
  }, []);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && url && !loading) handleScan();
  }, [url, loading, handleScan]);

  const getStatusText = useCallback(() => {
    switch (scanStatus) {
      case 'idle':      return '> READY';
      case 'scanning':  return scanType === 'standards'
        ? '> SCANNING ALL STANDARDS (this may take a minute)...'
        : scanType === 'ncsa'
        ? '> SCANNING สกมช. (NCSA Guidelines)...'
        : '> SCANNING...';
      case 'analyzing': return '> AI CYBERSECURITY ANALYSIS IN PROGRESS...';
      case 'done':      return '> SCAN COMPLETE';
      case 'error':     return '> ERROR';
    }
  }, [scanStatus, scanType]);

  const getStatusClass = useCallback(() => {
    switch (scanStatus) {
      case 'idle':      return '';
      case 'scanning':  return 'scanning';
      case 'analyzing': return 'scanning';
      case 'done':      return 'ready';
      case 'error':     return 'error';
    }
  }, [scanStatus]);

  const showResult = !!(result && !result.error);

  return {
    url, setUrl,
    lastScannedUrl,
    result,
    loading,
    scanStatus,
    scanType,
    resultsByType,
    expandedMap, setExpandedMap,
    handleSelectScanType,
    handleScan,
    handleReset,
    handleKeyDown,
    getStatusText,
    getStatusClass,
    showResult,
    aiBatchReady,
  };
}
