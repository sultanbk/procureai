/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Highlights matching text excerpts from invoices/contracts.
 * 
 * What it means:
 * Evidence validator.
 * 
 * Importance in Project:
 * High. Anchors flagged errors to verified document clauses.
 */

import { Quote, AlertCircle, CheckSquare, Target } from 'lucide-react';
import Badge from './ui/Badge';

export default function EvidenceBlock({ finding }) {
  const {
    description, clause_reference, clause_text, quantity,
    unit_price_charged, unit_price_expected, line_total_charged,
    line_total_expected, delta, recommendation, confidence
  } = finding;

  const recVariant = recommendation === 'DISPUTE' ? 'critical' : recommendation === 'ESCALATE' ? 'high' : recommendation === 'MONITOR' ? 'medium' : 'default';
  const confidencePct = Math.round(confidence * 100);

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-lg p-5 text-sm space-y-5">
      <div className="flex items-start gap-3">
        <div className="p-2 bg-teal-50 text-teal-600 rounded-lg shrink-0"><AlertCircle className="h-4 w-4 stroke-[1.5]" /></div>
        <div>
          <p className="text-[10px] uppercase font-semibold text-slate-400 tracking-wide">Agent Assessment</p>
          <p className="text-slate-900 font-medium mt-0.5 leading-relaxed">{description}</p>
        </div>
      </div>

      {clause_text && (
        <div className="bg-white rounded-lg p-4 border border-slate-200 relative">
          <Quote className="absolute right-3 top-3 h-8 w-8 text-slate-200 stroke-[1.5]" />
          <p className="text-[10px] font-semibold text-teal-600 uppercase tracking-wide mb-2">Contract: {clause_reference || 'Clause Reference'}</p>
          <blockquote className="text-slate-600 italic font-mono text-xs border-l-4 border-teal-500 pl-3 leading-relaxed">
            &ldquo;{clause_text}&rdquo;
          </blockquote>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="bg-white p-4 rounded-lg border border-slate-200">
          <p className="text-[10px] uppercase font-semibold text-slate-400">Charged</p>
          <p className="text-xs text-slate-600 mt-1">{quantity} × ${parseFloat(unit_price_charged).toFixed(2)}</p>
          <p className="text-sm font-mono font-bold text-rose-600 mt-1">= ${parseFloat(line_total_charged).toLocaleString('en-US', { minimumFractionDigits: 2 })}</p>
        </div>
        <div className="bg-white p-4 rounded-lg border border-slate-200">
          <p className="text-[10px] uppercase font-semibold text-slate-400">Expected</p>
          <p className="text-xs text-slate-600 mt-1">{quantity} × ${parseFloat(unit_price_expected).toFixed(2)}</p>
          <p className="text-sm font-mono font-bold text-emerald-600 mt-1">= ${parseFloat(line_total_expected).toLocaleString('en-US', { minimumFractionDigits: 2 })}</p>
        </div>
        <div className="bg-rose-50 p-4 rounded-lg border border-rose-200">
          <p className="text-[10px] uppercase font-semibold text-rose-600">Leakage</p>
          <p className="text-base font-mono font-bold text-rose-700 mt-1">${parseFloat(Math.abs(delta)).toLocaleString('en-US', { minimumFractionDigits: 2 })}</p>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-200">
        <div className="flex items-center gap-2">
          <CheckSquare className="h-4 w-4 text-slate-400 stroke-[1.5]" />
          <span className="text-xs text-slate-500">Action:</span>
          <Badge variant={recVariant}>{recommendation}</Badge>
        </div>
        <div className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-lg border border-slate-200">
          <Target className="h-4 w-4 text-slate-400 stroke-[1.5]" />
          <span className="text-xs text-slate-500">Confidence</span>
          <div className="w-16 bg-slate-100 h-1.5 rounded-full overflow-hidden">
            <div className="h-full bg-teal-600 rounded-full" style={{ width: `${confidencePct}%` }} />
          </div>
          <span className="font-mono text-xs font-semibold text-slate-700">{confidencePct}%</span>
        </div>
      </div>
    </div>
  );
}
