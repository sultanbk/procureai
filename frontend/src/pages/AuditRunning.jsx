/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Displays active agent execution and real-time logs.
 * 
 * What it means:
 * Live progress tracker page.
 * 
 * Importance in Project:
 * High. Gives direct visibility into backend pipeline states.
 */

import { useEffect, useState } from 'react';
import { getAuditStatus, getAuditLogs } from '../api';
import AgentProgressBar from '../components/AgentProgressBar';
import AuditLogConsole from '../components/AuditLogConsole';
import {
  ArrowLeft,
  Loader2,
  RefreshCw,
  Cpu,
  Layers,
  ChevronDown,
  FileText,
  Clock,
  Building2,
  AlertTriangle,
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
  const [showLogs, setShowLogs] = useState(false);
  const [secondsElapsed, setSecondsElapsed] = useState(0);

  useEffect(() => {
    let isMounted = true;
    let completeTimeoutId = null;
    let intervalId = null;
    let ws = null;

    const startPolling = () => {
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
                const reportWithRulebook = { ...data.audit_report, rulebook: data.partial_results?.rulebook };
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
                    rulebook: msg.payload.partial_results?.rulebook
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

  // Live Timer Tracker synchronized with backend start timestamp
  useEffect(() => {
    if (!auditState) return;

    if (auditState.status === 'COMPLETE' || auditState.status === 'FAILED') {
      if (auditState.created_at && auditState.completed_at) {
        const start = parseUtcDate(auditState.created_at).getTime();
        const end = parseUtcDate(auditState.completed_at).getTime();
        setSecondsElapsed(Math.max(0, Math.round((end - start) / 1000)));
      }
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
  }, [auditState?.status, auditState?.created_at, auditState?.completed_at]);

  const STATUS_DETAILS = {
    PENDING: {
      title: 'Initializing Audit Pipeline',
      desc: 'Setting up agent models and preparing databases for document verification.',
      color: 'text-indigo-600',
    },
    EXTRACTING_PDF: {
      title: 'Digitizing Uploaded PDF Files',
      desc: 'OCRing pages and reading document layouts to convert files to structured texts.',
      color: 'text-cyan-600',
    },
    EXTRACTING_INVOICES: {
      title: 'Extracting Invoice Line Items',
      desc: 'AI invoice agent is reading billing descriptions, units, rates, and quantities.',
      color: 'text-amber-600',
    },
    PARSING_CONTRACT: {
      title: 'Analyzing Contract Billing Rules',
      desc: 'AI contract agent is building the ruleset, parsing unit caps, and pricing clauses.',
      color: 'text-sky-600',
    },
    CROSS_VALIDATING: {
      title: 'Cross-Referencing Line Rates',
      desc: 'Matching invoice line items against contract price rules to find billing mismatches.',
      color: 'text-violet-600',
    },
    CHECKING_COMPLIANCE: {
      title: 'Running Compliance Algorithms',
      desc: 'Scanning for service delivery delays, overcharges, and other revenue leakages.',
      color: 'text-teal-600',
    },
    GENERATING_REPORT: {
      title: 'Assembling Audit Report',
      desc: 'Compiling financial metrics, building charts, and drafting dispute recommendations.',
      color: 'text-emerald-600',
    },
    COMPLETE: {
      title: 'Audit Complete',
      desc: 'Verification workflow successfully concluded. Building dynamic findings report...',
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
      pdf_extractor: 'Layout Digitizer',
      invoice_extractor: 'Invoice Extractor',
      contract_parser: 'Contract Parser',
      cross_validator: 'Cross Validator',
      compliance_checker: 'Compliance Checker',
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

  if (!auditState && !error) {
    return (
      <div className="py-24 flex items-center justify-center">
        <Spinner label="Initializing verification agents..." />
      </div>
    );
  }

  const currentStatusInfo = STATUS_DETAILS[auditState?.status] || {
    title: 'Executing Audit Steps',
    desc: 'Processing validation rules and cross-referencing files.',
    color: 'text-teal-600'
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Top action header */}
      <div className="flex items-center justify-between pb-2">
        <Button variant="ghost" size="sm" onClick={onBack} className="hover:bg-slate-100/85">
          <ArrowLeft className="h-4 w-4 mr-1.5" /> Back to List
        </Button>
        <Badge variant="default" className="font-mono text-[10px] bg-slate-100 hover:bg-slate-150 text-slate-700 border-slate-200">
          ID: {auditId}
        </Badge>
      </div>

      {/* Main dashboard columns */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Left Side: Steps Visualizer & Logs */}
        <div className="lg:col-span-2 space-y-6">
          {auditState && (
            <AgentProgressBar
              status={auditState.status}
              currentAgent={auditState.current_agent}
              agentsCompleted={auditState.agents_completed}
              partialResults={auditState.partial_results}
              errorDetail={auditState.error_detail}
            />
          )}

          {/* Diagnostic Log panel */}
          <Card className="border border-slate-200 overflow-hidden shadow-sm">
            <button
              type="button"
              onClick={() => setShowLogs(!showLogs)}
              className="w-full flex items-center justify-between p-4 hover:bg-slate-50 transition-colors"
            >
              <div className="flex items-center gap-2.5 text-slate-700">
                <Layers className="h-4.5 w-4.5 text-teal-600 stroke-[1.75]" />
                <div className="text-left">
                  <h3 className="text-sm font-semibold text-slate-800">Advanced Diagnostic Logs</h3>
                  <p className="text-[10px] text-slate-400">Inspect real-time agent coordination traces ({logs.length} events logged)</p>
                </div>
              </div>

              <ChevronDown
                className={`h-4 w-4 text-slate-400 transition-transform duration-300 ${
                  showLogs ? 'rotate-180' : ''
                }`}
              />
            </button>

            {showLogs && (
              <div className="border-t border-slate-100 p-4 bg-slate-950">
                <AuditLogConsole logs={logs} />
              </div>
            )}
          </Card>
        </div>

        {/* Right Side: Active Status Summary & File Details */}
        <div className="space-y-6">
          {/* Active status card */}
          <Card className="p-6 flex flex-col items-center text-center shadow-sm relative overflow-hidden">
            {/* Status gradient background splash */}
            <div className={`absolute top-0 left-0 right-0 h-1.5 ${
              auditState?.status === 'FAILED' ? 'bg-rose-500' :
              auditState?.status === 'COMPLETE' ? 'bg-emerald-500' :
              'bg-gradient-to-r from-teal-500 to-indigo-500'
            }`} />

            <div className={`h-14 w-14 rounded-full flex items-center justify-center mb-4 mt-2 ${
              auditState?.status === 'FAILED' ? 'bg-rose-50 text-rose-600 border border-rose-200' :
              auditState?.status === 'COMPLETE' ? 'bg-emerald-50 text-emerald-600 border border-emerald-200' :
              'bg-teal-50 text-teal-600 border border-teal-200 shadow-sm'
            }`}>
              {auditState?.status !== 'COMPLETE' && auditState?.status !== 'FAILED' ? (
                <Loader2 className="h-6 w-6 animate-spin stroke-[2]" />
              ) : (
                <Cpu className="h-6 w-6 stroke-[1.75]" />
              )}
            </div>

            <h4 className="text-base font-bold text-slate-900 tracking-tight">
              {currentStatusInfo.title}
            </h4>
            <p className="text-xs text-slate-500 mt-2 px-1 leading-relaxed max-w-[240px]">
              {currentStatusInfo.desc}
            </p>

            <div className="mt-5 pt-4 border-t border-slate-100 w-full flex items-center justify-around text-slate-600">
              <div className="flex flex-col items-center">
                <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Elapsed Time</span>
                <span className="text-sm font-semibold text-slate-700 mt-1 flex items-center gap-1 font-mono">
                  <Clock className="h-3.5 w-3.5 text-teal-600" />
                  {formatElapsed(secondsElapsed)}
                </span>
              </div>
              <div className="h-8 w-px bg-slate-100" />
              <div className="flex flex-col items-center">
                <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Current Agent</span>
                <span className="text-xs font-semibold text-slate-700 mt-1 bg-slate-50 px-2 py-0.5 rounded border border-slate-100">
                  {getAgentLabel(auditState?.current_agent)}
                </span>
              </div>
            </div>
          </Card>

          {/* Target files card */}
          <Card className="p-5 shadow-sm space-y-4">
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest border-b border-slate-100 pb-2.5">
              Audited Documents
            </h4>
            
            {/* Vendor name */}
            <div className="flex items-start gap-3">
              <div className="p-2 bg-slate-50 rounded-lg border border-slate-100 flex-shrink-0">
                <Building2 className="h-4 w-4 text-indigo-500" />
              </div>
              <div>
                <p className="text-[10px] font-bold text-slate-400 uppercase">Vendor</p>
                <p className="text-xs font-semibold text-slate-800 mt-0.5">
                  {auditState?.supplier_name || 'Extracting from file...'}
                </p>
              </div>
            </div>

            {/* Contract filename */}
            <div className="flex items-start gap-3">
              <div className="p-2 bg-slate-50 rounded-lg border border-slate-100 flex-shrink-0">
                <FileText className="h-4 w-4 text-teal-600" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-[10px] font-bold text-slate-400 uppercase">Service Contract</p>
                <p className="text-xs font-semibold text-slate-800 mt-0.5 truncate hover:text-clip" title={auditState?.contract_file}>
                  {auditState?.contract_file || 'Loading contract...'}
                </p>
              </div>
            </div>

            {/* Invoices list */}
            <div className="flex items-start gap-3">
              <div className="p-2 bg-slate-50 rounded-lg border border-slate-100 flex-shrink-0">
                <FileText className="h-4 w-4 text-violet-500" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-[10px] font-bold text-slate-400 uppercase">
                  Audited Invoices ({auditState?.invoice_files?.length || 0})
                </p>
                <div className="mt-1 space-y-1">
                  {auditState?.invoice_files && auditState.invoice_files.length > 0 ? (
                    auditState.invoice_files.map((file, i) => (
                      <p key={i} className="text-xs font-medium text-slate-600 truncate" title={file}>
                        {file}
                      </p>
                    ))
                  ) : (
                    <p className="text-xs font-medium text-slate-500 italic">No invoices found</p>
                  )}
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Global workflow error */}
      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3.5 rounded-xl text-sm flex justify-between items-center shadow-sm">
          <span className="flex items-center gap-2 font-medium">
            <AlertTriangle className="h-4 w-4 text-rose-500" /> {error}
          </span>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="flex items-center gap-1 font-bold text-xs uppercase tracking-wider text-rose-800 bg-rose-100 hover:bg-rose-200 px-3 py-1.5 rounded-lg transition-colors"
          >
            <RefreshCw className="h-3 w-3" /> Reload Pipeline
          </button>
        </div>
      )}
    </div>
  );
}
