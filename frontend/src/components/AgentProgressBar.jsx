/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Progress bar displaying active pipeline statuses.
 * 
 * What it means:
 * Agent progress visualizer.
 * 
 * Importance in Project:
 * Medium. Provides visual feedback to users during live audits.
 */

import Card from './ui/Card';
import Badge from './ui/Badge';
import { Check, Loader2, AlertCircle, Hourglass, Play } from 'lucide-react';

export default function AgentProgressBar({ status, currentAgent, agentsCompleted, partialResults, errorDetail }) {
  const steps = [
    {
      id: 'invoice_extractor',
      name: 'Invoice Extractor',
      // description: 'Digitizes structure and extracts all invoice line items, rates, and quantities.', 
      agent: 'invoice_extractor',
      getDetails: () => partialResults?.invoice_line_count !== undefined ? `${partialResults.invoice_line_count} line items parsed` : null
    },
    {
      id: 'contract_parser',
      name: 'Contract Parser',
      // description: 'Parses legal terms, pricing tables, and SLA parameters.', 
      agent: 'contract_parser',
      getDetails: () => partialResults?.rulebook_rule_count !== undefined ? `${partialResults.rulebook_rule_count} rules extracted` : null
    },
    {
      id: 'cross_validator',
      name: 'Cross Validator',
      // description: 'Cross-checks extracted invoice quantities and rates against contract parameters.', 
      agent: 'cross_validator',
      getDetails: () => null
    },
    {
      id: 'compliance_checker',
      name: 'Compliance Checker',
      // description: 'Runs leakage detection algorithms and billing compliance checks.', 
      agent: 'compliance_checker',
      getDetails: () => null
    },
    {
      id: 'report_generator',
      name: 'Report Generator',
      // description: 'Aggregates all agent findings into a final PDF report and audit summary.', 
      agent: 'report_generator',
      getDetails: () => null
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
    if (currentAgent === step.agent || (step.agent === 'invoice_extractor' && (status === 'EXTRACTING_PDF' || status === 'PENDING'))) return 'active';
    return 'pending';
  };

  const getStatusLabel = (rawStatus) => {
    const statusMap = {
      PENDING: 'Initializing Pipeline',
      EXTRACTING_PDF: 'Digitizing Files',
      EXTRACTING_INVOICES: 'Extracting Invoice Data',
      PARSING_CONTRACT: 'Parsing Contract Rules',
      CROSS_VALIDATING: 'Cross-Referencing Line Items',
      CHECKING_COMPLIANCE: 'Analyzing Billing Compliance',
      GENERATING_REPORT: 'Generating Report',
      COMPLETE: 'Audit Completed',
      FAILED: 'Pipeline Failed'
    };
    return statusMap[rawStatus] || rawStatus.replace(/_/g, ' ');
  };

  const progressWidth = status === 'COMPLETE' ? '100%' :
    status === 'FAILED' ? `${(steps.findIndex(s => s.agent === currentAgent) / (steps.length - 1)) * 100}%` :
      `${(agentsCompleted.length / (steps.length - 1)) * 100}%`;

  return (
    <Card className="p-6 overflow-hidden">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center border-b border-slate-100 pb-5 mb-8 gap-4">
        <div>
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest font-sans">Verification Pipeline</span>
          <h3 className="text-xl font-display font-bold text-slate-900 mt-1 flex items-center gap-2">
            Status: <span className="text-teal-600 font-sans font-semibold">{getStatusLabel(status)}</span>
          </h3>
        </div>
        {status !== 'COMPLETE' && status !== 'FAILED' ? (
          <Badge variant="brand" className="animate-pulse bg-teal-500/10 text-teal-700 border border-teal-500/20 px-3 py-1 flex items-center gap-1.5 font-semibold text-xs rounded-full">
            <span className="h-1.5 w-1.5 rounded-full bg-teal-500 block animate-ping" />
            Analyzing Documents
          </Badge>
        ) : status === 'COMPLETE' ? (
          <Badge variant="success" className="bg-emerald-500/10 text-emerald-700 border border-emerald-500/20 px-3 py-1 font-semibold text-xs rounded-full">
            Ready
          </Badge>
        ) : (
          <Badge variant="danger" className="bg-rose-500/10 text-rose-700 border border-rose-500/20 px-3 py-1 font-semibold text-xs rounded-full">
            Halted
          </Badge>
        )}
      </div>

      {/* Stepper container */}
      <div className="relative flex flex-col md:flex-row justify-between gap-8 md:gap-4 md:px-2">
        {/* Connection Line */}
        <div className="hidden md:block absolute top-5 left-10 right-10 h-1 bg-slate-100 rounded-full z-0">
          <div
            className="h-full bg-gradient-to-r from-teal-500 to-emerald-500 transition-all duration-700 ease-out rounded-full shadow-[0_0_8px_rgba(20,184,166,0.3)]"
            style={{ width: progressWidth }}
          />
        </div>

        {steps.map((step, idx) => {
          const state = getStepState(step, idx);
          const details = step.getDetails();

          return (
            <div key={step.id} className="flex flex-row md:flex-col items-start md:items-center gap-4 md:gap-0 relative z-10 flex-1 group">
              {/* Node Icon */}
              <div className="flex-shrink-0 md:mx-auto mb-0 md:mb-3">
                {state === 'completed' && (
                  <div className="h-10 w-10 rounded-full bg-emerald-500 text-white flex items-center justify-center shadow-[0_4px_12px_rgba(16,185,129,0.2)] border-2 border-white transition-all duration-300">
                    <Check className="h-5 w-5 stroke-[2.5]" />
                  </div>
                )}

                {state === 'active' && (
                  <div className="relative">
                    {/* Ring glow animation */}
                    <div className="absolute -inset-1.5 rounded-full bg-teal-500/20 animate-ping" />
                    <div className="relative h-10 w-10 rounded-full bg-teal-600 text-white flex items-center justify-center border-2 border-white shadow-[0_4px_12px_rgba(13,148,136,0.3)]">
                      <Loader2 className="h-5 w-5 animate-spin" />
                    </div>
                  </div>
                )}

                {state === 'failed' && (
                  <div className="h-10 w-10 rounded-full bg-rose-500 text-white flex items-center justify-center shadow-[0_4px_12px_rgba(239,68,68,0.2)] border-2 border-white">
                    <AlertCircle className="h-5 w-5" />
                  </div>
                )}

                {state === 'pending' && (
                  <div className="h-10 w-10 rounded-full bg-slate-50 border-2 border-slate-200 text-slate-400 flex items-center justify-center transition-colors group-hover:border-slate-300">
                    <Hourglass className="h-4 w-4 stroke-[1.5]" />
                  </div>
                )}
              </div>

              {/* Step Text details */}
              <div className="md:text-center flex-1">
                <h4 className={`text-xs font-bold uppercase tracking-wider transition-colors ${state === 'active' ? 'text-teal-600' :
                    state === 'completed' ? 'text-emerald-700' :
                      state === 'failed' ? 'text-rose-600' : 'text-slate-400'
                  }`}>
                  {step.name}
                </h4>
                <p className="text-[11px] text-slate-500 mt-1 md:max-w-[145px] md:mx-auto leading-relaxed">
                  {step.description}
                </p>

                {state === 'active' && !details && (
                  <span className="inline-block mt-2 text-[9px] font-bold text-teal-600 uppercase tracking-widest bg-teal-50 px-2 py-0.5 rounded border border-teal-100 animate-pulse">
                    Processing
                  </span>
                )}

                {details && (
                  <Badge variant="success" className="mt-2 text-[9px] font-mono font-bold bg-emerald-50 text-emerald-700 border border-emerald-100">
                    {details.toUpperCase()}
                  </Badge>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {status === 'FAILED' && errorDetail && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 p-4 rounded-xl mt-8 flex flex-col gap-2">
          <span className="font-bold uppercase tracking-wider text-xs text-rose-800 flex items-center gap-1.5">
            <AlertCircle className="h-4 w-4" /> Pipeline Error Details
          </span>
          <p className="font-mono text-xs mt-1 whitespace-pre-wrap leading-relaxed bg-white/50 p-3 rounded-lg border border-rose-100">
            {errorDetail}
          </p>
        </div>
      )}
    </Card>
  );
}

