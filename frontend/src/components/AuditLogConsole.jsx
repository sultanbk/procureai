/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Simulates a scrolling retro terminal displaying real-time agent output.
 * 
 * What it means:
 * Console console capturing pipeline logging telemetry.
 * 
 * Importance in Project:
 * High. Offers clear agent visibility to audit admins.
 */

import { useEffect, useRef, useState } from 'react';
import { Terminal, Copy, Check } from 'lucide-react';

export default function AuditLogConsole({ logs }) {
  const scrollContainerRef = useRef(null);
  const [copied, setCopied] = useState(false);

useEffect(() => {
  const container = scrollContainerRef.current;

  if (!container) return;

  const isNearBottom =
    container.scrollHeight -
      container.scrollTop -
      container.clientHeight <
    100;

  if (isNearBottom) {
    container.scrollTop = container.scrollHeight;
  }
}, [logs]);

  const copyToClipboard = () => {
    const text = logs
      .map(
        (log) =>
          `[${formatTime(log.timestamp)}] [${log.level}] [${
            log.agent ? log.agent.toUpperCase() : 'SYSTEM'
          }] ${log.message}`
      )
      .join('\n');
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formatTime = (isoString) => {
    try {
      const date = new Date(isoString);
      return date.toTimeString().split(' ')[0]; // HH:MM:SS
    } catch {
      return '00:00:00';
    }
  };

  const getAgentStyles = (agent) => {
    switch (agent) {
      case 'contract_parser':
        return 'text-cyan-700 bg-cyan-50 border-cyan-200';
      case 'invoice_extractor':
        return 'text-amber-700 bg-amber-50 border-amber-200';
      case 'cross_validator':
        return 'text-indigo-700 bg-indigo-50 border-indigo-200';
      case 'compliance_checker':
        return 'text-teal-700 bg-teal-50 border-teal-200';
      case 'report_generator':
        return 'text-emerald-700 bg-emerald-50 border-emerald-200';
      case 'pdf_extractor':
        return 'text-rose-700 bg-rose-50 border-rose-200';
      default:
        return 'text-slate-600 bg-slate-50 border-slate-200';
    }
  };

  const getAgentLabel = (agent) => {
    switch (agent) {
      case 'contract_parser':
        return 'Contract Parser';
      case 'invoice_extractor':
        return 'Invoice Extractor';
      case 'cross_validator':
        return 'Cross Validator';
      case 'compliance_checker':
        return 'Compliance Checker';
      case 'report_generator':
        return 'Report Generator';
      case 'pdf_extractor':
        return 'PDF Extractor';
      default:
        return 'System';
    }
  };

  const getLevelColor = (level) => {
    switch (level) {
      case 'WARNING':
        return 'text-amber-700 bg-amber-50 border-amber-200';
      case 'ERROR':
        return 'text-rose-700 bg-rose-50 border-rose-200';
      default:
        return 'text-slate-500 bg-slate-100 border-slate-200';
    }
  };

  return (
    <div className="w-full bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm flex flex-col font-mono text-xs leading-relaxed relative">

      {/* Console Header */}
      <div className="bg-slate-50 border-b border-slate-200 px-4 py-3 flex items-center justify-between select-none">

        {/* Terminal Dot Controls & Title */}
        <div className="flex items-center gap-3">

          <div className="flex items-center gap-1.5 select-none print:hidden">
            <span className="h-2.5 w-2.5 rounded-full bg-rose-400/80 block" />
            <span className="h-2.5 w-2.5 rounded-full bg-amber-400/80 block" />
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-400/80 block" />
          </div>

          <div className="flex items-center gap-2">
            <Terminal className="h-4 w-4 text-teal-600 stroke-[1.5]" />
            <span className="font-semibold text-slate-800 font-sans tracking-wide text-sm">Coordinator Stream Log</span>
            <span className="flex h-1.5 w-1.5 relative select-none">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-teal-500" />
            </span>
          </div>
        </div>

        {/* Copy Button */}
        {logs.length > 0 && (
          <button
            type="button"
            onClick={copyToClipboard}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-slate-500 hover:text-slate-800 bg-white border border-slate-250 hover:bg-slate-50 shadow-sm transition-all font-sans text-xs font-semibold"
            title="Copy all logs"
          >
            {copied ? (
              <>
                <Check className="h-3 w-3 text-emerald-600 stroke-[1.5]" />
                <span className="text-emerald-600">Copied!</span>
              </>
            ) : (
              <>
                <Copy className="h-3 w-3 stroke-[1.5]" />
                <span>Copy Console</span>
              </>
            )}
          </button>
        )}
      </div>

      {/* Console Output Stream */}
      <div
        ref={scrollContainerRef}
        className="flex-1 p-4 space-y-2 max-h-80 overflow-y-auto min-h-[180px] bg-slate-50/30 scrollbar-thin scrollbar-thumb-slate-200 scrollbar-track-transparent"
      >
        {logs.length === 0 ? (
          <div className="h-full flex items-center justify-center text-slate-400 py-14 select-none">
            <span className="animate-pulse">Awaiting coordinator stream logs...</span>
          </div>
        ) : (
          logs.map((log, index) => (
            <div key={log.id || index} className="flex items-start gap-2 hover:bg-slate-100/50 p-1 rounded-md transition-colors">
              {/* Timestamp */}
              <span className="text-slate-400 select-none flex-shrink-0 font-mono font-medium">
                [{formatTime(log.timestamp)}]
              </span>

              {/* Log Level Warning/Error Badges */}
              {log.level !== 'INFO' && (
                <span
                  className={`inline-flex px-1.5 py-0.5 rounded border text-[10px] font-bold leading-tight flex-shrink-0 ${getLevelColor(
                    log.level
                  )}`}
                >
                  {log.level}
                </span>
              )}

              {/* Emitter Pill */}
              <span className={`px-2 py-0.5 rounded border text-[10px] font-bold leading-none flex-shrink-0 tracking-wide font-sans ${getAgentStyles(log.agent)}`}>
                {getAgentLabel(log.agent)}
              </span>

              {/* Message */}
              <span className="text-slate-700 break-all leading-relaxed font-mono font-medium">
                {log.message}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
