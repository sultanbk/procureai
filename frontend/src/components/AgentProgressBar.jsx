/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Interactive multi-agent pipeline progress visualization and stage inspector.
 * 
 * What it means:
 * Mission-control visual tracker for live document ingestion, OCR, parsing, cross-validation,
 * compliance checking, and executive report synthesis.
 * 
 * Importance in Project:
 * High. Primary visual interface communicating agent activity and verification state to users.
 */

import Card from './ui/Card';
import Badge from './ui/Badge';
import {
  Check,
  Loader2,
  AlertCircle,
  Hourglass,
  FileText,
  ShieldAlert,
  Sparkles,
  Layers,
  ArrowRight,
} from 'lucide-react';

export default function AgentProgressBar({
  status,
  currentAgent,
  agentsCompleted = [],
  partialResults = {},
  errorDetail,
  onSelectAgent,
  selectedAgent = null,
  progressPct = null,
}) {
  const steps = [
    {
      id: 'pdf_extractor',
      name: 'Document OCR',
      shortName: 'OCR',
      description: 'Digitizes document layouts and converts raw PDFs to clean text structures.',
      agent: 'pdf_extractor',
      icon: FileText,
      getDetails: () => {
        if (agentsCompleted.includes('pdf_extractor') || currentAgent !== 'pdf_extractor') {
          return 'Layout digitized';
        }
        return 'Extracting text';
      }
    },
    {
      id: 'invoice_extractor',
      name: 'Invoice Extractor',
      shortName: 'Invoices',
      description: 'Reads line descriptions, quantities, unit prices, and validates arithmetic.',
      agent: 'invoice_extractor',
      icon: Layers,
      getDetails: () =>
        partialResults?.invoice_line_count !== undefined
          ? `${partialResults.invoice_line_count} line items parsed`
          : null
    },
    {
      id: 'contract_parser',
      name: 'Contract Parser',
      shortName: 'Contract',
      description: 'Builds master rulebook, extracts clause thresholds, caps, and rate tables.',
      agent: 'contract_parser',
      icon: FileText,
      getDetails: () =>
        partialResults?.rulebook_rule_count !== undefined
          ? `${partialResults.rulebook_rule_count} rules extracted`
          : null
    },
    {
      id: 'cross_validator',
      name: 'Cross Validator',
      shortName: 'Cross-Check',
      description: 'Cross-references invoice lines against contract pricing rules and caps.',
      agent: 'cross_validator',
      icon: ArrowRight,
      getDetails: () => {
        if (partialResults?.invoice_line_count !== undefined && (agentsCompleted.includes('cross_validator') || currentAgent === 'compliance_checker')) {
          return `${partialResults.invoice_line_count} lines verified`;
        }
        return null;
      }
    },
    {
      id: 'compliance_checker',
      name: 'Compliance Critic',
      shortName: 'Compliance',
      description: 'Runs leakage detection algorithms, delivery SLA tests, and AI critic checks.',
      agent: 'compliance_checker',
      icon: ShieldAlert,
      getDetails: () => {
        if (partialResults?.discrepancy_count !== undefined) {
          return `${partialResults.discrepancy_count} discrepancies`;
        }
        return null;
      }
    },
    {
      id: 'report_generator',
      name: 'Report Generator',
      shortName: 'Synthesis',
      description: 'Assembles financial risk scorecards, dispute recommendations, and executive summaries.',
      agent: 'report_generator',
      icon: Sparkles,
      getDetails: () => {
        if (partialResults?.potential_leakage !== undefined && partialResults.potential_leakage > 0) {
          return `$${Number(partialResults.potential_leakage).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} flagged`;
        }
        return null;
      }
    },
  ];

  const getStepState = (step, idx) => {
    if (status === 'FAILED') {
      const currentIdx = steps.findIndex(s => s.agent === currentAgent);
      if (idx === currentIdx) return 'failed';
      if (idx < currentIdx) return 'completed';
      return 'pending';
    }
    if (status === 'COMPLETE') return 'completed';
    if (agentsCompleted.includes(step.agent)) return 'completed';
    if (currentAgent === step.agent || (step.agent === 'pdf_extractor' && (status === 'EXTRACTING_PDF' || status === 'PENDING'))) return 'active';
    return 'pending';
  };

  const getStatusLabel = (rawStatus) => {
    const statusMap = {
      PENDING: 'Initializing Pipeline',
      EXTRACTING_PDF: 'Digitizing PDF Documents',
      EXTRACTING_INVOICES: 'Extracting Invoice Line Items',
      PARSING_CONTRACT: 'Analyzing Contract Rulebook',
      CROSS_VALIDATING: 'Cross-Referencing Line Rates',
      CHECKING_COMPLIANCE: 'Running Compliance Algorithms',
      GENERATING_REPORT: 'Assembling Final Audit Report',
      COMPLETE: 'Audit Completed Successfully',
      FAILED: 'Pipeline Terminated with Error'
    };
    return statusMap[rawStatus] || rawStatus.replace(/_/g, ' ');
  };

  // Derive progress percentage
  const computedProgress = (() => {
    if (typeof progressPct === 'number' && progressPct >= 0) return progressPct;
    if (status === 'COMPLETE') return 100;
    if (status === 'FAILED') {
      const failedIdx = steps.findIndex(s => s.agent === currentAgent);
      return Math.round((Math.max(0, failedIdx) / steps.length) * 100);
    }
    const completedCount = agentsCompleted.length;
    const isStepActive = steps.some(s => s.agent === currentAgent);
    const activeBonus = isStepActive ? 0.5 : 0;
    return Math.min(95, Math.round(((completedCount + activeBonus) / steps.length) * 100));
  })();

  return (
    <Card className="p-6 overflow-hidden border border-slate-200/80 shadow-sm bg-white">
      {/* Top Header with Live Status & Percentage */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center border-b border-slate-100 pb-5 mb-6 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest font-sans">
              Verification Pipeline
            </span>
            <span className="h-1 w-1 rounded-full bg-slate-300" />
            <span className="text-[11px] font-mono font-semibold text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-100">
              {computedProgress}% Complete
            </span>
          </div>
          <h3 className="text-xl font-display font-bold text-slate-900 mt-1 flex items-center gap-2">
            <span className="text-teal-600 font-sans font-semibold">
              {getStatusLabel(status)}
            </span>
          </h3>
        </div>

        <div className="flex items-center gap-3">
          {status !== 'COMPLETE' && status !== 'FAILED' ? (
            <Badge
              variant="brand"
              className="bg-teal-500/10 text-teal-700 border border-teal-500/20 px-3 py-1 flex items-center gap-2 font-semibold text-xs rounded-full shadow-xs"
            >
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-teal-500" />
              </span>
              Analyzing Documents
            </Badge>
          ) : status === 'COMPLETE' ? (
            <Badge
              variant="success"
              className="bg-emerald-500/10 text-emerald-700 border border-emerald-500/20 px-3.5 py-1 font-semibold text-xs rounded-full flex items-center gap-1.5"
            >
              <Check className="h-3.5 w-3.5 stroke-[2.5]" />
              Audit Complete
            </Badge>
          ) : (
            <Badge
              variant="danger"
              className="bg-rose-500/10 text-rose-700 border border-rose-500/20 px-3.5 py-1 font-semibold text-xs rounded-full flex items-center gap-1.5"
            >
              <AlertCircle className="h-3.5 w-3.5" />
              Pipeline Terminated
            </Badge>
          )}
        </div>
      </div>

      {/* Progress Bar Gauge */}
      <div className="mb-8">
        <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden shadow-inner relative">
          <div
            className={`h-full transition-all duration-700 ease-out rounded-full ${
              status === 'FAILED'
                ? 'bg-rose-500'
                : status === 'COMPLETE'
                ? 'bg-emerald-500'
                : 'bg-gradient-to-r from-teal-500 via-cyan-500 to-emerald-500'
            }`}
            style={{ width: `${computedProgress}%` }}
          />
        </div>
        <div className="flex justify-between items-center text-[10px] text-slate-400 font-mono mt-1.5 px-0.5">
          <span>Stage 1: OCR & Ingestion</span>
          <span>Stage 3: Cross-Validation</span>
          <span>Stage 6: Report</span>
        </div>
      </div>

      {/* Stepper Pipeline Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 relative">
        {steps.map((step, idx) => {
          const state = getStepState(step, idx);
          const details = step.getDetails();
          const isSelected = selectedAgent === step.agent;

          return (
            <div
              key={step.id}
              onClick={() => onSelectAgent && onSelectAgent(isSelected ? null : step.agent)}
              className={`p-3.5 rounded-xl border transition-all duration-200 cursor-pointer flex flex-col justify-between select-none relative group ${
                isSelected
                  ? 'ring-2 ring-teal-500 border-teal-500 bg-teal-50/40 shadow-sm'
                  : state === 'active'
                  ? 'border-teal-400 bg-teal-50/30 shadow-md shadow-teal-500/5'
                  : state === 'completed'
                  ? 'border-emerald-200/80 bg-emerald-50/20 hover:border-emerald-300'
                  : state === 'failed'
                  ? 'border-rose-300 bg-rose-50/30'
                  : 'border-slate-200/70 bg-slate-50/50 hover:border-slate-300 hover:bg-slate-50'
              }`}
              title={`Click to filter logs for ${step.name}`}
            >
              {/* Top Node Indicator & Status */}
              <div className="flex items-center justify-between mb-2.5">
                <div className="flex items-center gap-1.5">
                  <span className="text-[10px] font-mono font-bold text-slate-400">
                    0{idx + 1}
                  </span>
                </div>

                {/* State Icon Badge */}
                <div>
                  {state === 'completed' && (
                    <div className="h-6 w-6 rounded-full bg-emerald-500 text-white flex items-center justify-center shadow-xs">
                      <Check className="h-3.5 w-3.5 stroke-[2.5]" />
                    </div>
                  )}

                  {state === 'active' && (
                    <div className="relative">
                      <span className="animate-ping absolute -inset-1 rounded-full bg-teal-400/40 block" />
                      <div className="relative h-6 w-6 rounded-full bg-teal-600 text-white flex items-center justify-center shadow-sm">
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      </div>
                    </div>
                  )}

                  {state === 'failed' && (
                    <div className="h-6 w-6 rounded-full bg-rose-500 text-white flex items-center justify-center shadow-xs">
                      <AlertCircle className="h-3.5 w-3.5" />
                    </div>
                  )}

                  {state === 'pending' && (
                    <div className="h-6 w-6 rounded-full bg-slate-100 border border-slate-200 text-slate-400 flex items-center justify-center group-hover:border-slate-300">
                      <Hourglass className="h-3 w-3 stroke-[1.5]" />
                    </div>
                  )}
                </div>
              </div>

              {/* Step Info */}
              <div>
                <h4
                  className={`text-xs font-bold leading-tight ${
                    state === 'active'
                      ? 'text-teal-700'
                      : state === 'completed'
                      ? 'text-slate-800'
                      : state === 'failed'
                      ? 'text-rose-700'
                      : 'text-slate-500'
                  }`}
                >
                  {step.name}
                </h4>

                <p className="text-[10px] text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                  {step.description}
                </p>
              </div>

              {/* Dynamic Bottom Sub-metrics */}
              <div className="mt-3 pt-2 border-t border-slate-100/80 flex items-center justify-between">
                {state === 'active' && !details && (
                  <span className="text-[9px] font-bold text-teal-600 uppercase tracking-wider animate-pulse">
                    Executing...
                  </span>
                )}

                {details ? (
                  <span
                    className={`text-[9px] font-mono font-semibold truncate ${
                      state === 'completed'
                        ? 'text-emerald-700'
                        : state === 'active'
                        ? 'text-teal-700 font-bold'
                        : 'text-slate-500'
                    }`}
                  >
                    {details}
                  </span>
                ) : state === 'completed' ? (
                  <span className="text-[9px] font-mono font-medium text-emerald-600">
                    Done
                  </span>
                ) : state === 'pending' ? (
                  <span className="text-[9px] font-mono text-slate-400">
                    Waiting
                  </span>
                ) : null}

                {isSelected && (
                  <span className="text-[8px] uppercase tracking-wider font-bold bg-teal-600 text-white px-1 rounded">
                    Filtered
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Failure Diagnostic Alert */}
      {status === 'FAILED' && errorDetail && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 p-4 rounded-xl mt-6 flex flex-col gap-2 shadow-xs">
          <span className="font-bold uppercase tracking-wider text-xs text-rose-800 flex items-center gap-1.5">
            <AlertCircle className="h-4 w-4" /> Pipeline Exception Details
          </span>
          <p className="font-mono text-xs mt-1 whitespace-pre-wrap leading-relaxed bg-white/70 p-3 rounded-lg border border-rose-100 text-rose-950 select-text">
            {errorDetail}
          </p>
        </div>
      )}
    </Card>
  );
}
