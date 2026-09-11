/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Live audit execution dashboard with real-time multi-agent orchestration telemetry.
 * 
 * What it means:
 * Mission-control live monitoring center tracking document OCR, extraction, cross-validation,
 * compliance checking, and report generation in real-time.
 * 
 * Importance in Project:
 * High. Primary active workspace while audit pipelines are executing.
 */

import { useEffect, useState, useMemo } from 'react';
import { getAuditStatus, getAuditLogs } from '../api';
import AgentProgressBar from '../components/AgentProgressBar';
import AuditLogConsole from '../components/AuditLogConsole';
import {
  ArrowLeft,
  Loader2,
  RefreshCw,
  Cpu,
  Layers,
  FileText,
  Clock,
  Building2,
  AlertTriangle,
  Copy,
  Check,
  Radio,
  FileSpreadsheet,
  DollarSign,
  ShieldCheck,
  ChevronRight,
  Activity,
} from 'lucide-react';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Spinner from '../components/ui/Spinner';
import Badge from '../components/ui/Badge';

const parseUtcDate = (dateStr) => {
  if (!dateStr) return null;
  if (dateStr.endsWith('Z') || dateStr.includes('+') || (dateStr.includes('-') && dateStr.lastIndexOf('-') > 10)) {
    return new Date(dateStr);
  }
  return new Date(`${dateStr}Z`);
};

export default function AuditRunning({ auditId, onBack, onComplete }) {
  const [auditState, setAuditState] = useState(null);
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState('');
  const [showLogs, setShowLogs] = useState(true);
  const [secondsElapsed, setSecondsElapsed] = useState(0);
  const [connectionStatus, setConnectionStatus] = useState('connecting'); // 'connected' | 'polling' | 'connecting'
  const [copiedId, setCopiedId] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [showBackConfirm, setShowBackConfirm] = useState(false);

  useEffect(() => {
    let isMounted = true;
    let completeTimeoutId = null;
    let intervalId = null;
    let ws = null;

    const startPolling = () => {
      setConnectionStatus('polling');
      const pollStatus = async () => {
        try {
          const data = await getAuditStatus(auditId);
          if (!isMounted) return;
          setAuditState(data);
          setError('');
          try {
            const logData = await getAuditLogs(auditId);
            if (isMounted) setLogs(logData);
          } catch (logErr) {
            console.error('Failed to fetch logs:', logErr);
          }
          if (data.status === 'COMPLETE') {
            clearInterval(intervalId);
            completeTimeoutId = setTimeout(() => {
              if (isMounted) {
                const reportWithRulebook = {
                  ...data.audit_report,
                  rulebook: data.audit_report?.rulebook || data.partial_results?.rulebook,
                  invoice_data: data.audit_report?.invoice_data || data.partial_results?.invoice_data
                };
                onComplete(reportWithRulebook);
              }
            }, 800);
          } else if (data.status === 'FAILED') {
            clearInterval(intervalId);
          }
        } catch (err) {
          if (isMounted) setError(err.message || 'Failed to poll audit status');
        }
      };

      pollStatus();
      intervalId = setInterval(pollStatus, 2000);
    };

    const baseApi = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
    const wsScheme = baseApi.startsWith("https") ? "wss" : "ws";
    const cleanBase = baseApi.replace(/^https?:\/\//, "");
    const wsUrl = `${wsScheme}://${cleanBase}/api/audit/${auditId}/ws`;

    try {
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        if (!isMounted) return;
        setConnectionStatus('connected');
      };

      ws.onmessage = (event) => {
        if (!isMounted) return;
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'status') {
            setAuditState(msg.payload);
            setError('');
            if (msg.payload.status === 'COMPLETE') {
              ws.close();
              completeTimeoutId = setTimeout(() => {
                if (isMounted) {
                  const reportWithRulebook = {
                    ...msg.payload.audit_report,
                    rulebook: msg.payload.audit_report?.rulebook || msg.payload.partial_results?.rulebook,
                    invoice_data: msg.payload.audit_report?.invoice_data || msg.payload.partial_results?.invoice_data
                  };
                  onComplete(reportWithRulebook);
                }
              }, 800);
            }
          } else if (msg.type === 'log') {
            setLogs((prev) => {
              const isDuplicate = prev.some(
                (l) => l.timestamp === msg.payload.timestamp && l.message === msg.payload.message
              );
              if (isDuplicate) return prev;
              return [...prev, msg.payload].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
            });
          } else if (msg.type === 'error') {
            setError(msg.payload.detail || 'An error occurred during audit');
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onerror = () => {
        if (!isMounted) return;
        startPolling();
      };

      ws.onclose = () => {
        if (isMounted && auditState?.status !== 'COMPLETE' && auditState?.status !== 'FAILED') {
          startPolling();
        }
      };
    } catch (err) {
      console.error('Failed to initialize WebSocket:', err);
      startPolling();
    }

    return () => {
      isMounted = false;
      if (ws) ws.close();
      if (intervalId) clearInterval(intervalId);
      if (completeTimeoutId) clearTimeout(completeTimeoutId);
    };
  }, [auditId, onComplete]);

  // Final elapsed time derived when audit has finished; otherwise dynamic seconds
  const displaySeconds = (() => {
    if ((auditState?.status === 'COMPLETE' || auditState?.status === 'FAILED') && auditState?.created_at && auditState?.completed_at) {
      const start = parseUtcDate(auditState.created_at).getTime();
      const end = parseUtcDate(auditState.completed_at).getTime();
      return Math.max(0, Math.round((end - start) / 1000));
    }
    return secondsElapsed;
  })();

  // Live Timer Tracker synchronized with backend start timestamp
  useEffect(() => {
    if (!auditState || auditState.status === 'COMPLETE' || auditState.status === 'FAILED') {
      return;
    }

    const startTime = auditState.created_at ? parseUtcDate(auditState.created_at).getTime() : Date.now();

    const updateTimer = () => {
      const elapsed = Math.round((Date.now() - startTime) / 1000);
      setSecondsElapsed(Math.max(0, elapsed));
    };

    updateTimer();
    const timerInterval = setInterval(updateTimer, 1000);

    return () => clearInterval(timerInterval);
  }, [auditState]);

  const STATUS_DETAILS = {
    PENDING: {
      title: 'Initializing Audit Pipeline',
      desc: 'Orchestrating agent models, loading rule registries, and priming telemetry queues.',
      color: 'text-indigo-600',
    },
    EXTRACTING_PDF: {
      title: 'Digitizing Uploaded PDF Files',
      desc: 'Performing layout OCR and structural character mapping on contracts and invoices.',
      color: 'text-cyan-600',
    },
    EXTRACTING_INVOICES: {
      title: 'Extracting Invoice Line Items',
      desc: 'Parsing line descriptions, unit rates, quantities, and running arithmetic cross-checks.',
      color: 'text-amber-600',
    },
    PARSING_CONTRACT: {
      title: 'Synthesizing Contract Rulebook',
      desc: 'Extracting clause thresholds, rate schedules, volume rebate tiers, and SLA penalty rules.',
      color: 'text-sky-600',
    },
    CROSS_VALIDATING: {
      title: 'Cross-Referencing Line Rates',
      desc: 'Matching invoice line items against contractual rulebooks to detect rate & quantity deviations.',
      color: 'text-violet-600',
    },
    CHECKING_COMPLIANCE: {
      title: 'Evaluating Billing Compliance',
      desc: 'Scanning for service delivery delays, unauthorized fees, and executing AI critic reviews.',
      color: 'text-teal-600',
    },
    GENERATING_REPORT: {
      title: 'Synthesizing Executive Audit Report',
      desc: 'Aggregating financial leakage metrics, supplier scorecard ratings, and dispute arguments.',
      color: 'text-emerald-600',
    },
    COMPLETE: {
      title: 'Audit Complete',
      desc: 'Verification workflow successfully concluded. Directing to dynamic findings report...',
      color: 'text-emerald-600',
    },
    FAILED: {
      title: 'Pipeline Terminated',
      desc: 'An error occurred during multi-agent audit execution. See logs below for troubleshooting.',
      color: 'text-rose-600',
    }
  };

  const getAgentLabel = (agent) => {
    const labels = {
      init: 'Supervisor Core',
      pdf_extractor: 'Document OCR',
      invoice_extractor: 'Invoice Extractor',
      contract_parser: 'Contract Parser',
      cross_validator: 'Cross Validator',
      compliance_checker: 'Compliance Critic',
      report_generator: 'Report Generator'
    };
    return labels[agent] || 'Supervisor Core';
  };

  const formatElapsed = (sec) => {
    if (sec < 60) return `${sec}s`;
    const mins = Math.floor(sec / 60);
    const secs = sec % 60;
    return `${mins}m ${secs}s`;
  };

  const copyAuditId = () => {
    navigator.clipboard.writeText(auditId);
    setCopiedId(true);
    setTimeout(() => setCopiedId(false), 2000);
  };

  // Get latest log message for live activity ticker
  const latestLog = useMemo(() => {
    if (logs.length === 0) return null;
    return logs[logs.length - 1];
  }, [logs]);

  const handleBackClick = () => {
    const isRunning = auditState && auditState.status !== 'COMPLETE' && auditState.status !== 'FAILED';
    if (isRunning && !showBackConfirm) {
      setShowBackConfirm(true);
      return;
    }
    onBack();
  };

  if (!auditState && !error) {
    return (
      <div className="py-28 flex flex-col items-center justify-center gap-4">
        <Spinner label="Initializing multi-agent audit pipeline..." />
        <p className="text-xs text-slate-400 font-mono">Establishing WebSocket telemetry stream...</p>
      </div>
    );
  }

  const currentStatusInfo = STATUS_DETAILS[auditState?.status] || {
    title: 'Executing Audit Steps',
    desc: 'Processing validation rules and cross-referencing files.',
    color: 'text-teal-600'
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-12 animate-fade-in">
      {/* ── Top Mission Control Header ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-2 border-b border-slate-200/80">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleBackClick}
            className="hover:bg-slate-100 text-slate-600 font-sans"
          >
            <ArrowLeft className="h-4 w-4 mr-1.5" /> Back to List
          </Button>

          {showBackConfirm && (
            <div className="flex items-center gap-2 bg-amber-50 text-amber-800 text-xs px-2.5 py-1 rounded-md border border-amber-200">
              <span>Pipeline is active. Leave anyway?</span>
              <button
                type="button"
                onClick={onBack}
                className="font-bold underline hover:text-amber-950"
              >
                Yes, leave
              </button>
              <button
                type="button"
                onClick={() => setShowBackConfirm(false)}
                className="text-slate-500 hover:text-slate-800 ml-1"
              >
                Cancel
              </button>
            </div>
          )}
        </div>

        {/* Status Indicators & Metadata */}
        <div className="flex items-center gap-2.5 flex-wrap">
          {/* WebSocket connection status indicator */}
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-sans font-medium border ${
              connectionStatus === 'connected'
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : connectionStatus === 'polling'
                ? 'bg-amber-50 text-amber-700 border-amber-200'
                : 'bg-slate-100 text-slate-600 border-slate-200'
            }`}
          >
            <span className="relative flex h-2 w-2">
              {connectionStatus === 'connected' && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              )}
              <span
                className={`relative inline-flex rounded-full h-2 w-2 ${
                  connectionStatus === 'connected'
                    ? 'bg-emerald-500'
                    : connectionStatus === 'polling'
                    ? 'bg-amber-500'
                    : 'bg-slate-400'
                }`}
              />
            </span>
            <span>
              {connectionStatus === 'connected'
                ? 'Telemetry Live'
                : connectionStatus === 'polling'
                ? 'Polling Sync'
                : 'Connecting...'}
            </span>
          </div>

          {/* Audit ID Badge with Copy */}
          <button
            type="button"
            onClick={copyAuditId}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-full font-mono text-[11px] bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition-colors"
            title="Click to copy Audit ID"
          >
            {copiedId ? (
              <>
                <Check className="h-3 w-3 text-emerald-600" />
                <span className="text-emerald-700 font-semibold">ID Copied!</span>
              </>
            ) : (
              <>
                <Copy className="h-3 w-3 text-slate-400" />
                <span>{auditId}</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* ── Multi-Agent Progress Visualizer ── */}
      {auditState && (
        <AgentProgressBar
          status={auditState.status}
          currentAgent={auditState.current_agent}
          agentsCompleted={auditState.agents_completed || []}
          partialResults={auditState.partial_results || {}}
          errorDetail={auditState.error_detail}
          onSelectAgent={setSelectedAgent}
          selectedAgent={selectedAgent}
          progressPct={auditState.progress_pct}
        />
      )}

      {/* ── Main Dashboard Layout ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Left Side (2 cols): Active Mission Status & Advanced Telemetry Console */}
        <div className="lg:col-span-2 space-y-6">
          {/* Active Mission Card with Live Stream Ticker */}
          <Card className="p-5 border border-slate-200/90 shadow-sm relative overflow-hidden bg-gradient-to-br from-white to-slate-50/60">
            {/* Top Accent Gradient Bar */}
            <div
              className={`absolute top-0 left-0 right-0 h-1.5 ${
                auditState?.status === 'FAILED'
                  ? 'bg-rose-500'
                  : auditState?.status === 'COMPLETE'
                  ? 'bg-emerald-500'
                  : 'bg-gradient-to-r from-teal-500 via-cyan-500 to-indigo-500'
              }`}
            />

            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="flex items-start gap-3.5">
                <div
                  className={`h-11 w-11 rounded-xl flex items-center justify-center flex-shrink-0 shadow-xs ${
                    auditState?.status === 'FAILED'
                      ? 'bg-rose-50 text-rose-600 border border-rose-200'
                      : auditState?.status === 'COMPLETE'
                      ? 'bg-emerald-50 text-emerald-600 border border-emerald-200'
                      : 'bg-teal-50 text-teal-600 border border-teal-200'
                  }`}
                >
                  {auditState?.status !== 'COMPLETE' && auditState?.status !== 'FAILED' ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : auditState?.status === 'COMPLETE' ? (
                    <ShieldCheck className="h-5 w-5" />
                  ) : (
                    <AlertTriangle className="h-5 w-5" />
                  )}
                </div>

                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider font-sans">
                      Active Task
                    </span>
                    <span className="h-1 w-1 rounded-full bg-slate-300" />
                    <span className="text-[11px] font-semibold text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-100 font-sans">
                      {getAgentLabel(auditState?.current_agent)}
                    </span>
                  </div>
                  <h4 className="text-base font-bold text-slate-900 mt-0.5">
                    {currentStatusInfo.title}
                  </h4>
                  <p className="text-xs text-slate-500 mt-0.5 leading-relaxed max-w-xl">
                    {currentStatusInfo.desc}
                  </p>
                </div>
              </div>

              {/* Execution Clock Widget */}
              <div className="flex items-center gap-3 self-end sm:self-center bg-white px-3 py-2 rounded-lg border border-slate-200/80 shadow-xs font-mono">
                <Clock className="h-4 w-4 text-teal-600" />
                <div className="text-right">
                  <p className="text-[9px] uppercase font-bold text-slate-400 tracking-wider">
                    Elapsed
                  </p>
                  <p className="text-sm font-bold text-slate-800">
                    {formatElapsed(displaySeconds)}
                  </p>
                </div>
              </div>
            </div>

            {/* Live Activity Stream Ticker */}
            {latestLog && auditState?.status !== 'COMPLETE' && auditState?.status !== 'FAILED' && (
              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center gap-2.5 text-xs text-slate-600 bg-slate-100/50 p-2.5 rounded-lg border border-slate-200/60 font-mono">
                <Activity className="h-3.5 w-3.5 text-teal-600 animate-pulse flex-shrink-0" />
                <span className="text-[10px] uppercase font-bold text-teal-700 bg-teal-50 px-1.5 py-0.5 rounded border border-teal-200 flex-shrink-0">
                  Latest Action
                </span>
                <span className="text-slate-800 truncate text-[11px] select-text">
                  {latestLog.message}
                </span>
              </div>
            )}
          </Card>

          {/* Advanced Diagnostic Logs Section */}
          <div className="space-y-2">
            <div className="flex items-center justify-between px-1">
              <div className="flex items-center gap-2">
                <Layers className="h-4 w-4 text-teal-600" />
                <h3 className="text-sm font-bold text-slate-800 font-sans">
                  Advanced Diagnostic Logs & Traces
                </h3>
                <span className="text-[11px] font-mono text-slate-400">
                  ({logs.length} events recorded)
                </span>
              </div>

              <div className="flex items-center gap-2">
                {selectedAgent && (
                  <button
                    type="button"
                    onClick={() => setSelectedAgent(null)}
                    className="text-[11px] text-teal-600 hover:text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200 font-sans font-medium"
                  >
                    Clear agent filter ({getAgentLabel(selectedAgent)})
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => setShowLogs(!showLogs)}
                  className="text-xs text-slate-500 hover:text-slate-800 font-sans font-medium"
                >
                  {showLogs ? 'Minimize Console' : 'Expand Console'}
                </button>
              </div>
            </div>

            {showLogs && (
              <AuditLogConsole
                logs={logs}
                selectedAgent={selectedAgent}
                onSelectAgent={setSelectedAgent}
                title="ProcureAI Multi-Agent Coordination Stream"
              />
            )}
          </div>
        </div>

        {/* Right Side (1 col): Live Telemetry KPIs & Audited Documents */}
        <div className="space-y-6">
          {/* Live Findings & Extracted Artifacts KPI card */}
          <Card className="p-5 border border-slate-200/90 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest font-sans">
                Live Extraction Telemetry
              </h4>
              <span className="h-2 w-2 rounded-full bg-teal-500 animate-ping" />
            </div>

            <div className="grid grid-cols-2 gap-2.5">
              {/* Rules extracted */}
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                <div className="flex items-center gap-1.5 text-slate-400 text-[10px] font-bold uppercase">
                  <FileText className="h-3 w-3 text-sky-500" />
                  <span>Contract Rules</span>
                </div>
                <p className="text-lg font-bold font-mono text-slate-800 mt-1">
                  {auditState?.partial_results?.rulebook_rule_count !== undefined
                    ? auditState.partial_results.rulebook_rule_count
                    : '—'}
                </p>
              </div>

              {/* Invoice lines */}
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                <div className="flex items-center gap-1.5 text-slate-400 text-[10px] font-bold uppercase">
                  <Layers className="h-3 w-3 text-amber-500" />
                  <span>Invoice Lines</span>
                </div>
                <p className="text-lg font-bold font-mono text-slate-800 mt-1">
                  {auditState?.partial_results?.invoice_line_count !== undefined
                    ? auditState.partial_results.invoice_line_count
                    : '—'}
                </p>
              </div>

              {/* Discrepancies */}
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                <div className="flex items-center gap-1.5 text-slate-400 text-[10px] font-bold uppercase">
                  <AlertTriangle className="h-3 w-3 text-rose-500" />
                  <span>Flagged Findings</span>
                </div>
                <p className="text-lg font-bold font-mono text-slate-800 mt-1">
                  {auditState?.partial_results?.discrepancy_count !== undefined
                    ? auditState.partial_results.discrepancy_count
                    : '—'}
                </p>
              </div>

              {/* Potential leakage */}
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                <div className="flex items-center gap-1.5 text-slate-400 text-[10px] font-bold uppercase">
                  <DollarSign className="h-3 w-3 text-emerald-500" />
                  <span>Potential Delta</span>
                </div>
                <p className="text-lg font-bold font-mono text-slate-800 mt-1">
                  {auditState?.partial_results?.potential_leakage !== undefined
                    ? `$${Number(auditState.partial_results.potential_leakage).toLocaleString(undefined, { maximumFractionDigits: 0 })}`
                    : '—'}
                </p>
              </div>
            </div>
          </Card>

          {/* Audited Documents Card */}
          <Card className="p-5 border border-slate-200/90 shadow-sm space-y-4">
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest border-b border-slate-100 pb-2.5 font-sans">
              Audited Documents
            </h4>

            {/* Vendor Name */}
            <div className="flex items-start gap-3">
              <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg border border-indigo-100 flex-shrink-0">
                <Building2 className="h-4 w-4" />
              </div>
              <div>
                <p className="text-[10px] font-bold text-slate-400 uppercase">Vendor</p>
                <p className="text-xs font-semibold text-slate-800 mt-0.5">
                  {auditState?.supplier_name || 'Extracting from file...'}
                </p>
              </div>
            </div>

            {/* Master Contract File */}
            <div className="flex items-start gap-3">
              <div className="p-2 bg-teal-50 text-teal-600 rounded-lg border border-teal-100 flex-shrink-0">
                <FileSpreadsheet className="h-4 w-4" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-[10px] font-bold text-slate-400 uppercase">Master Contract</p>
                <p
                  className="text-xs font-semibold text-slate-800 mt-0.5 truncate"
                  title={auditState?.contract_file}
                >
                  {auditState?.contract_file || 'Loading contract...'}
                </p>
              </div>
            </div>

            {/* Invoices List */}
            <div className="flex items-start gap-3">
              <div className="p-2 bg-violet-50 text-violet-600 rounded-lg border border-violet-100 flex-shrink-0">
                <FileText className="h-4 w-4" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between">
                  <p className="text-[10px] font-bold text-slate-400 uppercase">
                    Invoices ({auditState?.invoice_files?.length || 0})
                  </p>
                </div>
                <div className="mt-1.5 space-y-1 max-h-36 overflow-y-auto pr-1 scrollbar-thin">
                  {auditState?.invoice_files && auditState.invoice_files.length > 0 ? (
                    auditState.invoice_files.map((file, i) => (
                      <div
                        key={i}
                        className="text-xs font-medium text-slate-600 truncate bg-slate-50 px-2 py-1 rounded border border-slate-100 flex items-center gap-1.5"
                        title={file}
                      >
                        <span className="text-[9px] font-mono font-bold text-slate-400">
                          #{i + 1}
                        </span>
                        <span className="truncate">{file}</span>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs font-medium text-slate-400 italic">No invoices loaded</p>
                  )}
                </div>
              </div>
            </div>
          </Card>

          {/* Multi-Agent Architecture Guide Info Box */}
          <Card className="p-4 bg-slate-50/70 border border-slate-200/80 shadow-xs space-y-2">
            <h5 className="text-[11px] font-bold uppercase tracking-wider text-slate-600 flex items-center gap-1.5">
              <Cpu className="h-3.5 w-3.5 text-teal-600" />
              Multi-Agent Architecture
            </h5>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              ProcureAI dispatches specialized AI agents in parallel: OCR digits, extractor agents validate arithmetic, contract agents parse pricing tiers, and cross-validators calculate net variance against legal clauses.
            </p>
          </Card>
        </div>
      </div>

      {/* ── Global Pipeline Failure Alert Banner ── */}
      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3.5 rounded-xl text-sm flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 shadow-sm animate-fade-in">
          <span className="flex items-center gap-2 font-medium">
            <AlertTriangle className="h-4 w-4 text-rose-500 flex-shrink-0" />
            <span>{error}</span>
          </span>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="flex items-center gap-1.5 font-bold text-xs uppercase tracking-wider text-rose-800 bg-rose-100 hover:bg-rose-200 px-3 py-1.5 rounded-lg transition-colors flex-shrink-0"
          >
            <RefreshCw className="h-3.5 w-3.5" /> Reload Pipeline
          </button>
        </div>
      )}
    </div>
  );
}
