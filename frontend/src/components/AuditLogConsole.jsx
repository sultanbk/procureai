/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Advanced telemetry and diagnostic log console with live grep search, level/agent filtering,
 * smart auto-scroll, relative/absolute timestamps, and forensic export tools.
 * 
 * What it means:
 * Real-time developer & auditor mission-control log viewer.
 * 
 * Importance in Project:
 * High. Offers transparent agent visibility, observability, and debugging tools.
 */

import { useEffect, useRef, useState, useMemo } from 'react';
import {
  Terminal,
  Copy,
  Check,
  Search,
  X,
  ArrowDown,
  Download,
  AlertTriangle,
  AlertCircle,
  Filter,
  Clock,
  ChevronDown,
  ChevronUp,
  Maximize2,
  Minimize2,
} from 'lucide-react';

export default function AuditLogConsole({
  logs = [],
  selectedAgent: externalSelectedAgent = null,
  onSelectAgent: externalOnSelectAgent = null,
  title = "Coordinator Telemetry Stream",
  className = "",
}) {
  const scrollContainerRef = useRef(null);
  const [copied, setCopied] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [levelFilter, setLevelFilter] = useState('ALL'); // ALL, INFO, WARNING, ERROR
  const [internalSelectedAgent, setInternalSelectedAgent] = useState('ALL');
  const [autoScroll, setAutoScroll] = useState(true);
  const [hasNewLogsWhilePaused, setHasNewLogsWhilePaused] = useState(false);
  const [timeMode, setTimeMode] = useState('wall'); // 'wall' (HH:MM:SS) or 'relative' (+X.Xs)
  const [expandedLogId, setExpandedLogId] = useState(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const prevLogsLengthRef = useRef(logs.length);

  // Sync external selectedAgent with internal agent filter if provided
  const activeAgentFilter = externalSelectedAgent !== null ? (externalSelectedAgent || 'ALL') : internalSelectedAgent;

  const handleAgentFilterChange = (agent) => {
    if (externalOnSelectAgent) {
      externalOnSelectAgent(agent === 'ALL' ? null : agent);
    }
    setInternalSelectedAgent(agent);
  };

  // Compute log counts by level
  const stats = useMemo(() => {
    let infoCount = 0;
    let warningCount = 0;
    let errorCount = 0;
    logs.forEach((log) => {
      if (log.level === 'WARNING') warningCount++;
      else if (log.level === 'ERROR') errorCount++;
      else infoCount++;
    });
    return {
      total: logs.length,
      info: infoCount,
      warning: warningCount,
      error: errorCount,
    };
  }, [logs]);

  // Derive first log timestamp for relative time calculation
  const firstTimestampMs = useMemo(() => {
    if (logs.length === 0) return null;
    const firstDate = new Date(logs[0].timestamp);
    return isNaN(firstDate.getTime()) ? null : firstDate.getTime();
  }, [logs]);

  // Filter logs based on search query, level filter, and agent filter
  const filteredLogs = useMemo(() => {
    return logs.filter((log) => {
      // Level filter
      if (levelFilter !== 'ALL' && log.level !== levelFilter) {
        return false;
      }
      // Agent filter
      if (activeAgentFilter !== 'ALL') {
        const logAgent = log.agent || 'system';
        if (logAgent !== activeAgentFilter) {
          return false;
        }
      }
      // Text search
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const msgMatches = log.message?.toLowerCase().includes(query);
        const agentMatches = log.agent?.toLowerCase().includes(query);
        const levelMatches = log.level?.toLowerCase().includes(query);
        if (!msgMatches && !agentMatches && !levelMatches) {
          return false;
        }
      }
      return true;
    });
  }, [logs, levelFilter, activeAgentFilter, searchQuery]);

  // Handle scroll events to detect if user manually scrolled up
  const handleScroll = () => {
    const container = scrollContainerRef.current;
    if (!container) return;
    const isAtBottom =
      container.scrollHeight - container.scrollTop - container.clientHeight < 40;
    if (isAtBottom) {
      setAutoScroll(true);
      setHasNewLogsWhilePaused(false);
    } else {
      setAutoScroll(false);
    }
  };

  // Manage auto-scroll when new logs arrive
  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;

    if (logs.length > prevLogsLengthRef.current) {
      if (autoScroll) {
        container.scrollTop = container.scrollHeight;
        setHasNewLogsWhilePaused(false);
      } else {
        setHasNewLogsWhilePaused(true);
      }
    }
    prevLogsLengthRef.current = logs.length;
  }, [logs, autoScroll]);

  const scrollToBottom = () => {
    const container = scrollContainerRef.current;
    if (container) {
      container.scrollTop = container.scrollHeight;
      setAutoScroll(true);
      setHasNewLogsWhilePaused(false);
    }
  };

  const jumpToLatestError = () => {
    const errorIdx = filteredLogs.findLastIndex((l) => l.level === 'ERROR');
    if (errorIdx !== -1) {
      const container = scrollContainerRef.current;
      const errorElem = document.getElementById(`log-item-${errorIdx}`);
      if (errorElem && container) {
        errorElem.scrollIntoView({ behavior: 'smooth', block: 'center' });
        setAutoScroll(false);
      }
    }
  };

  const copyToClipboard = () => {
    const text = filteredLogs
      .map(
        (log, idx) =>
          `[${formatTime(log.timestamp, idx)}] [${log.level || 'INFO'}] [${(
            log.agent || 'SYSTEM'
          ).toUpperCase()}] ${log.message}`
      )
      .join('\n');
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadLogs = (asJson = false) => {
    let blob;
    let filename = `audit-telemetry-${new Date().toISOString().replace(/[:.]/g, '-')}`;
    if (asJson) {
      blob = new Blob([JSON.stringify(filteredLogs, null, 2)], {
        type: 'application/json',
      });
      filename += '.json';
    } else {
      const text = filteredLogs
        .map(
          (log, idx) =>
            `[${formatTime(log.timestamp, idx)}] [${log.level || 'INFO'}] [${(
              log.agent || 'SYSTEM'
            ).toUpperCase()}] ${log.message}`
        )
        .join('\n');
      blob = new Blob([text], { type: 'text/plain' });
      filename += '.log';
    }
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const formatTime = (isoString, idx) => {
    if (timeMode === 'relative' && firstTimestampMs) {
      try {
        const date = new Date(isoString);
        const diffSec = Math.max(0, (date.getTime() - firstTimestampMs) / 1000);
        return `+${diffSec.toFixed(1)}s`;
      } catch {
        return `+${idx * 0.5}s`;
      }
    }
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
        return 'text-cyan-400 bg-cyan-950/60 border-cyan-800/80';
      case 'invoice_extractor':
        return 'text-amber-400 bg-amber-950/60 border-amber-800/80';
      case 'cross_validator':
        return 'text-indigo-400 bg-indigo-950/60 border-indigo-800/80';
      case 'compliance_checker':
        return 'text-teal-300 bg-teal-950/60 border-teal-800/80';
      case 'report_generator':
        return 'text-emerald-400 bg-emerald-950/60 border-emerald-800/80';
      case 'pdf_extractor':
        return 'text-violet-400 bg-violet-950/60 border-violet-800/80';
      default:
        return 'text-slate-400 bg-slate-900 border-slate-700/80';
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
        return 'Compliance Critic';
      case 'report_generator':
        return 'Report Generator';
      case 'pdf_extractor':
        return 'Document OCR';
      default:
        return 'Supervisor Core';
    }
  };

  // Helper to highlight matching text inside logs
  const renderHighlightedMessage = (text) => {
    if (!searchQuery.trim()) return text;
    const parts = text.split(new RegExp(`(${escapeRegExp(searchQuery)})`, 'gi'));
    return parts.map((part, i) =>
      part.toLowerCase() === searchQuery.toLowerCase() ? (
        <mark
          key={i}
          className="bg-amber-400 text-slate-950 font-bold px-0.5 rounded-xs"
        >
          {part}
        </mark>
      ) : (
        part
      )
    );
  };

  function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  const agentsList = [
    { id: 'ALL', name: 'All Agents' },
    { id: 'system', name: 'Supervisor Core' },
    { id: 'pdf_extractor', name: 'Document OCR' },
    { id: 'invoice_extractor', name: 'Invoice Extractor' },
    { id: 'contract_parser', name: 'Contract Parser' },
    { id: 'cross_validator', name: 'Cross Validator' },
    { id: 'compliance_checker', name: 'Compliance Critic' },
    { id: 'report_generator', name: 'Report Generator' },
  ];

  return (
    <div
      className={`w-full bg-slate-950 border border-slate-800/80 rounded-xl overflow-hidden shadow-2xl flex flex-col font-mono text-xs leading-relaxed relative ${
        isFullscreen ? 'fixed inset-4 z-50 shadow-2xl h-[calc(100vh-2rem)]' : ''
      } ${className}`}
    >
      {/* ── Top Terminal Bar: Dots, Title, Live Status, Controls ── */}
      <div className="bg-slate-900/90 border-b border-slate-800 px-4 py-2.5 flex flex-wrap items-center justify-between gap-3 select-none backdrop-blur-md">
        {/* Left: Window Dots & Header */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="h-3 w-3 rounded-full bg-rose-500/80 border border-rose-600/40 inline-block" />
            <span className="h-3 w-3 rounded-full bg-amber-500/80 border border-amber-600/40 inline-block" />
            <span className="h-3 w-3 rounded-full bg-emerald-500/80 border border-emerald-600/40 inline-block" />
          </div>

          <div className="flex items-center gap-2 text-slate-200">
            <Terminal className="h-4 w-4 text-teal-400 stroke-[1.75]" />
            <span className="font-semibold font-sans tracking-wide text-xs text-slate-100">
              {title}
            </span>
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-teal-400" />
            </span>
          </div>

          <span className="hidden sm:inline-block text-[10px] text-slate-400 font-mono border-l border-slate-800 pl-3">
            {stats.total} total traces
          </span>
        </div>

        {/* Right: Telemetry Quick Action Buttons */}
        <div className="flex items-center gap-1.5">
          {/* Timestamp mode switch */}
          <button
            type="button"
            onClick={() => setTimeMode(timeMode === 'wall' ? 'relative' : 'wall')}
            className="flex items-center gap-1 px-2 py-1 rounded bg-slate-800/80 hover:bg-slate-800 text-slate-300 border border-slate-700/70 text-[11px] font-sans font-medium transition-colors"
            title="Toggle wall-clock vs relative execution timestamp"
          >
            <Clock className="h-3 w-3 text-slate-400" />
            <span>{timeMode === 'wall' ? 'Wall Clock' : 'Relative (+s)'}</span>
          </button>

          {/* Jump to latest error if errors exist */}
          {stats.error > 0 && (
            <button
              type="button"
              onClick={jumpToLatestError}
              className="flex items-center gap-1 px-2 py-1 rounded bg-rose-950/60 hover:bg-rose-900/60 text-rose-300 border border-rose-800/80 text-[11px] font-sans font-medium transition-colors animate-pulse"
              title="Jump to latest error trace"
            >
              <AlertCircle className="h-3 w-3 text-rose-400" />
              <span>Jump Error</span>
            </button>
          )}

          {/* Copy logs */}
          <button
            type="button"
            onClick={copyToClipboard}
            className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700/80 text-[11px] font-sans font-medium transition-colors shadow-xs"
            title="Copy filtered logs to clipboard"
          >
            {copied ? (
              <>
                <Check className="h-3 w-3 text-emerald-400" />
                <span className="text-emerald-400 font-semibold">Copied</span>
              </>
            ) : (
              <>
                <Copy className="h-3 w-3 text-slate-400" />
                <span>Copy</span>
              </>
            )}
          </button>

          {/* Download Logs Dropdown / Button */}
          <button
            type="button"
            onClick={() => downloadLogs(false)}
            className="flex items-center gap-1 px-2 py-1 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700/80 text-[11px] font-sans font-medium transition-colors"
            title="Download trace logs as text file"
          >
            <Download className="h-3 w-3 text-slate-400" />
            <span className="hidden sm:inline">Export</span>
          </button>

          {/* Fullscreen Toggle */}
          <button
            type="button"
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-1 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-slate-200 border border-slate-700/80 transition-colors"
            title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
          >
            {isFullscreen ? <Minimize2 className="h-3 w-3" /> : <Maximize2 className="h-3 w-3" />}
          </button>
        </div>
      </div>

      {/* ── Filter & Search Toolbar ── */}
      <div className="bg-slate-900/60 border-b border-slate-800/80 px-4 py-2 flex flex-wrap items-center justify-between gap-3 select-none">
        {/* Level Filters Chips */}
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => setLevelFilter('ALL')}
            className={`px-2 py-0.5 rounded text-[10px] font-sans font-semibold transition-colors ${
              levelFilter === 'ALL'
                ? 'bg-teal-500/20 text-teal-300 border border-teal-500/40'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            ALL ({stats.total})
          </button>

          <button
            type="button"
            onClick={() => setLevelFilter('INFO')}
            className={`px-2 py-0.5 rounded text-[10px] font-sans font-semibold transition-colors ${
              levelFilter === 'INFO'
                ? 'bg-sky-500/20 text-sky-300 border border-sky-500/40'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            INFO ({stats.info})
          </button>

          <button
            type="button"
            onClick={() => setLevelFilter('WARNING')}
            className={`px-2 py-0.5 rounded text-[10px] font-sans font-semibold transition-colors flex items-center gap-1 ${
              levelFilter === 'WARNING'
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                : 'text-amber-400/70 hover:text-amber-300 hover:bg-slate-800/50'
            }`}
          >
            <AlertTriangle className="h-2.5 w-2.5" />
            WARN ({stats.warning})
          </button>

          <button
            type="button"
            onClick={() => setLevelFilter('ERROR')}
            className={`px-2 py-0.5 rounded text-[10px] font-sans font-semibold transition-colors flex items-center gap-1 ${
              levelFilter === 'ERROR'
                ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                : 'text-rose-400/70 hover:text-rose-300 hover:bg-slate-800/50'
            }`}
          >
            <AlertCircle className="h-2.5 w-2.5" />
            ERROR ({stats.error})
          </button>
        </div>

        {/* Agent Filter Select & Search Box */}
        <div className="flex items-center gap-2 flex-1 max-w-md justify-end">
          {/* Agent dropdown */}
          <div className="relative">
            <select
              value={activeAgentFilter}
              onChange={(e) => handleAgentFilterChange(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-slate-300 text-[11px] rounded px-2 py-1 pr-6 focus:outline-none focus:border-teal-500 appearance-none font-sans font-medium"
            >
              {agentsList.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
            </select>
            <ChevronDown className="h-3 w-3 text-slate-400 absolute right-1.5 top-2 pointer-events-none" />
          </div>

          {/* Grep Search Bar */}
          <div className="relative flex-1 min-w-[140px]">
            <Search className="h-3 w-3 text-slate-500 absolute left-2 top-2 pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search logs, tokens, errors..."
              className="w-full bg-slate-900/90 border border-slate-700/90 rounded text-slate-200 placeholder:text-slate-500 text-[11px] pl-7 pr-6 py-1 focus:outline-none focus:border-teal-500 font-mono"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                className="absolute right-1.5 top-1.5 text-slate-400 hover:text-slate-200"
              >
                <X className="h-3 w-3" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* ── Log Stream Window ── */}
      <div
        ref={scrollContainerRef}
        onScroll={handleScroll}
        className={`flex-1 p-3 space-y-1 overflow-y-auto min-h-[220px] bg-slate-950 font-mono text-[11px] select-text scrollbar-thin scrollbar-thumb-slate-800 scrollbar-track-transparent ${
          isFullscreen ? 'max-h-[calc(100vh-140px)]' : 'max-h-96'
        }`}
      >
        {filteredLogs.length === 0 ? (
          <div className="h-44 flex flex-col items-center justify-center text-slate-500 select-none">
            {logs.length === 0 ? (
              <>
                <span className="h-2 w-2 rounded-full bg-teal-400 animate-ping mb-2" />
                <span className="text-slate-400">Awaiting multi-agent coordination traces...</span>
              </>
            ) : (
              <>
                <Filter className="h-5 w-5 text-slate-600 mb-2" />
                <span className="text-slate-400">No logs match current filters.</span>
                <button
                  type="button"
                  onClick={() => {
                    setSearchQuery('');
                    setLevelFilter('ALL');
                    handleAgentFilterChange('ALL');
                  }}
                  className="mt-2 text-teal-400 hover:underline text-[10px] font-sans"
                >
                  Clear all filters
                </button>
              </>
            )}
          </div>
        ) : (
          filteredLogs.map((log, index) => {
            const isError = log.level === 'ERROR';
            const isWarning = log.level === 'WARNING';
            const isExpanded = expandedLogId === (log.id || index);

            return (
              <div
                key={log.id || index}
                id={`log-item-${index}`}
                onClick={() => setExpandedLogId(isExpanded ? null : (log.id || index))}
                className={`group flex items-start gap-2.5 px-2 py-1 rounded transition-colors cursor-pointer ${
                  isError
                    ? 'bg-rose-950/30 hover:bg-rose-950/50 border border-rose-900/40 text-rose-200'
                    : isWarning
                    ? 'bg-amber-950/25 hover:bg-amber-950/40 border border-amber-900/30 text-amber-200'
                    : 'hover:bg-slate-900/70 border border-transparent text-slate-300'
                }`}
              >
                {/* Line number */}
                <span className="text-slate-600 select-none font-mono text-[10px] w-7 text-right flex-shrink-0 pt-0.5">
                  {String(index + 1).padStart(3, '0')}
                </span>

                {/* Timestamp */}
                <span className="text-slate-500 select-none flex-shrink-0 font-mono text-[10px] pt-0.5">
                  [{formatTime(log.timestamp, index)}]
                </span>

                {/* Level Badge */}
                {log.level && log.level !== 'INFO' && (
                  <span
                    className={`inline-flex px-1 py-0.2 rounded border text-[9px] font-bold leading-tight flex-shrink-0 mt-0.5 ${
                      isError
                        ? 'text-rose-400 bg-rose-950/80 border-rose-800/80'
                        : 'text-amber-400 bg-amber-950/80 border-amber-800/80'
                    }`}
                  >
                    {log.level}
                  </span>
                )}

                {/* Emitter Agent Tag */}
                <span
                  className={`px-1.5 py-0.5 rounded border text-[9px] font-bold leading-none flex-shrink-0 tracking-wide font-sans mt-0.5 ${getAgentStyles(
                    log.agent
                  )}`}
                  title={`Emitted by ${getAgentLabel(log.agent)}`}
                >
                  {getAgentLabel(log.agent)}
                </span>

                {/* Log Message with grep highlighter */}
                <span
                  className={`flex-1 break-words leading-relaxed font-mono ${
                    isError
                      ? 'text-rose-200 font-medium'
                      : isWarning
                      ? 'text-amber-200 font-medium'
                      : 'text-slate-200'
                  }`}
                >
                  {renderHighlightedMessage(log.message)}
                </span>

                {/* Expand icon if message is long */}
                {log.message && log.message.length > 120 && (
                  <span className="text-slate-600 group-hover:text-slate-400 flex-shrink-0 pt-0.5">
                    {isExpanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                  </span>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* ── Auto-scroll Pause Floating Pill ── */}
      {hasNewLogsWhilePaused && (
        <div className="absolute bottom-10 right-6 z-20">
          <button
            type="button"
            onClick={scrollToBottom}
            className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold text-xs shadow-lg transition-transform hover:scale-105 animate-bounce font-sans"
          >
            <ArrowDown className="h-3.5 w-3.5" />
            <span>New traces below (click to jump)</span>
          </button>
        </div>
      )}

      {/* ── Bottom Console Status Bar ── */}
      <div className="bg-slate-900 border-t border-slate-800/90 px-4 py-1.5 flex items-center justify-between text-[10px] text-slate-400 select-none">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1">
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                autoScroll ? 'bg-emerald-400' : 'bg-amber-400'
              }`}
            />
            <span>Auto-scroll: {autoScroll ? 'Active' : 'Paused (Manual Scroll)'}</span>
          </span>

          {searchQuery && (
            <span className="text-teal-400 font-sans">
              Filtered: {filteredLogs.length} of {logs.length}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {!autoScroll && (
            <button
              type="button"
              onClick={scrollToBottom}
              className="text-teal-400 hover:underline flex items-center gap-0.5"
            >
              Resume Auto-Scroll <ArrowDown className="h-2.5 w-2.5" />
            </button>
          )}
          <span className="text-slate-600 font-mono">ProcureAI Telemetry v2.4</span>
        </div>
      </div>
    </div>
  );
}
