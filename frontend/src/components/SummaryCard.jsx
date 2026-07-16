/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Displays individual numbers and scores in grids.
 * 
 * What it means:
 * Metric card.
 * 
 * Importance in Project:
 * High. Visual summary block for dashboard statistics.
 */

import { Calendar, User, FileText, DollarSign, Award, ShieldCheck, AlertCircle, AlertTriangle, CheckCircle, Info } from 'lucide-react';
import Button from './ui/Button';
import Badge from './ui/Badge';
import Card from './ui/Card';
import Tooltip from './ui/Tooltip';

export default function SummaryCard({ summary, discrepancies = [], onGenerateDispute, children }) {
  const {
    supplier_name, contract_id, audit_date, billing_period, total_leakage,
    total_lines_audited, compliant_lines, discrepancy_count,
    critical_count, high_count, medium_count, executive_summary
  } = summary;

  const formattedDate = new Date(audit_date).toLocaleDateString('en-US', {
    day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
  });

  const totalLines = parseInt(total_lines_audited) || 0;
  const compLines = parseInt(compliant_lines) || 0;
  const complianceScore = totalLines > 0 ? Math.round((compLines / totalLines) * 100) : 100;

  let healthLabel = 'Optimal';
  let healthVariant = 'success';
  let healthIcon = <CheckCircle className="h-4 w-4 stroke-[1.5]" />;
  let strokeColor = '#10b981';
  let cardBorder = 'border-emerald-200';

  if (complianceScore < 80) {
    healthLabel = 'Requires Action'; healthVariant = 'critical';
    healthIcon = <AlertTriangle className="h-4 w-4 stroke-[1.5]" />; strokeColor = '#f43f5e'; cardBorder = 'border-rose-200';
  } else if (complianceScore < 95) {
    healthLabel = 'Good Compliance'; healthVariant = 'high';
    healthIcon = <AlertCircle className="h-4 w-4 stroke-[1.5]" />; strokeColor = '#f59e0b'; cardBorder = 'border-amber-200';
  }

  const radius = 38;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (complianceScore / 100) * circumference;

  return (
    <div className="flex flex-col gap-6 w-full">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 w-full">
      <Card className="border-rose-200 bg-rose-50/30">
        <div className="flex justify-between items-start mb-4">
          <div className="flex items-center gap-2">
            <Badge variant="critical">Recoverable Leakage</Badge>
            <Tooltip content="Total monetary discrepancies flagged in this audit that can potentially be recovered via disputes." position="right">
              <Info className="h-4 w-4 text-rose-400 hover:text-rose-600 cursor-help transition-colors stroke-[1.5]" />
            </Tooltip>
          </div>
          <div className="p-2 bg-rose-100 rounded-lg"><DollarSign className="h-5 w-5 text-rose-600 stroke-[1.5]" /></div>
        </div>
        <p className="text-xs text-slate-500 font-medium">Audit Leakage Flagged</p>
        <p className="text-3xl font-bold font-mono text-rose-700 mt-1">
          ${Math.abs(parseFloat(total_leakage)).toLocaleString('en-US', { minimumFractionDigits: 2 })}
        </p>
        {discrepancies?.some(d => d.recommendation === 'DISPUTE') && onGenerateDispute && (
          <Button variant="danger" size="sm" className="mt-4 w-full flex items-center justify-center gap-1.5 font-semibold" onClick={onGenerateDispute}>
            <FileText className="h-4 w-4 stroke-[1.5]" /> Generate Dispute Letter
          </Button>
        )}
        <div className="flex gap-2 mt-4 pt-4 border-t border-rose-200">
          {critical_count > 0 && <div className="flex-1 text-center"><Badge variant="critical">{critical_count} Critical</Badge></div>}
          {high_count > 0 && <div className="flex-1 text-center"><Badge variant="high">{high_count} High</Badge></div>}
          {medium_count > 0 && <div className="flex-1 text-center"><Badge variant="medium">{medium_count} Med</Badge></div>}
        </div>
        <div className="mt-4 pt-3 border-t border-rose-200 flex items-center justify-between text-xs text-rose-700">
          <div className="flex items-center gap-1.5">
            <span className="font-medium">Recoverable Disputes</span>
            <Tooltip content="The total number of individual line-item discrepancies flagged." position="top">
              <Info className="h-3.5 w-3.5 text-rose-400 hover:text-rose-600 cursor-help transition-colors stroke-[1.5]" />
            </Tooltip>
          </div>
          <span className="font-bold">{discrepancy_count}</span>
        </div>
      </Card>

      <Card className={cardBorder}>
        <div className="flex justify-between items-start mb-4">
          <div className="flex items-center gap-2">
            <Badge variant={healthVariant}>Compliance Score</Badge>
            <Tooltip content="The percentage of audited invoice lines that strictly comply with contract pricing, SLAs, and discounts." position="right">
              <Info className="h-4 w-4 text-slate-400 hover:text-slate-600 cursor-help transition-colors stroke-[1.5]" />
            </Tooltip>
          </div>
          <div className="p-2 bg-teal-50 rounded-lg"><ShieldCheck className="h-5 w-5 text-teal-600 stroke-[1.5]" /></div>
        </div>
        <div className="flex items-center gap-5">
          <div className="relative flex-shrink-0">
            <svg className="w-24 h-24 -rotate-90">
              <circle cx="48" cy="48" r={radius} stroke="#e2e8f0" strokeWidth="7" fill="transparent" />
              <circle cx="48" cy="48" r={radius} strokeWidth="7" strokeDasharray={circumference} strokeDashoffset={strokeDashoffset} strokeLinecap="round" stroke={strokeColor} fill="transparent" style={{ transition: 'stroke-dashoffset 0.8s ease' }} />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-xl font-bold font-mono text-slate-900">{complianceScore}</span>
              <span className="text-[8px] text-slate-400 uppercase font-semibold">score</span>
            </div>
          </div>
          <div>
            <Badge variant={healthVariant} className="mb-2">{healthIcon} {healthLabel}</Badge>
            <p className="text-xs text-slate-600 leading-relaxed">
              {totalLines > 0 ? `${compLines} of ${totalLines} audited checks passed contract validation.` : 'No invoice checks available.'}
            </p>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-2 mt-4 pt-4 border-t border-slate-200 text-center">
          <div><p className="text-[10px] text-slate-400 uppercase font-semibold">Audited</p><p className="text-sm font-bold font-mono text-slate-900">{totalLines}</p></div>
          <div><p className="text-[10px] text-slate-400 uppercase font-semibold">Compliant</p><p className="text-sm font-bold font-mono text-emerald-600">{compLines}</p></div>
          <div><p className="text-[10px] text-slate-400 uppercase font-semibold">Disputed</p><p className="text-sm font-bold font-mono text-rose-600">{discrepancy_count}</p></div>
        </div>
      </Card>

      <Card>
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-4 pb-2 border-b border-slate-200">Audit Particulars</p>
        <div className="space-y-3">
          <div className="flex items-center gap-3 text-sm">
            <User className="h-4 w-4 text-teal-600 shrink-0 stroke-[1.5]" />
            <div><p className="text-[10px] text-slate-400 uppercase font-semibold">Supplier</p><p className="font-semibold text-slate-900">{supplier_name}</p></div>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <FileText className="h-4 w-4 text-teal-600 shrink-0 stroke-[1.5]" />
            <div><p className="text-[10px] text-slate-400 uppercase font-semibold">Contract</p><p className="font-mono text-xs text-slate-700 truncate max-w-[180px]" title={contract_id}>{contract_id}</p></div>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <Calendar className="h-4 w-4 text-teal-600 shrink-0 stroke-[1.5]" />
            <div><p className="text-[10px] text-slate-400 uppercase font-semibold">Billing Period</p><p className="font-semibold text-slate-900">{billing_period}</p></div>
          </div>
        </div>
        <p className="text-[10px] text-slate-400 mt-4 pt-3 border-t border-slate-200 flex justify-between font-mono">
          <span>Processed</span><span>{formattedDate}</span>
        </p>
      </Card>

      </div>

      {children}

      {executive_summary && (
        <Card>
          <div className="flex items-center gap-2 mb-3 pb-2 border-b border-slate-200">
            <Award className="h-5 w-5 text-teal-600 stroke-[1.5]" />
            <h4 className="text-sm font-semibold text-slate-900">Executive Summary</h4>
          </div>
          <p className="text-sm text-slate-700 leading-relaxed bg-slate-50 p-4 rounded-lg border-l-4 border-teal-500 italic">
            &ldquo;{executive_summary}&rdquo;
          </p>
        </Card>
      )}
    </div>
  );
}
