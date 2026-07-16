/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Summarizes individual audit findings, logs, and billing errors.
 * 
 * What it means:
 * Audit report page.
 * 
 * Importance in Project:
 * High. The central screen displaying discrepancies and evidence.
 */

import { useState, useEffect, useMemo } from 'react';
import {
  ArrowLeft, Sparkles, FileCheck, Terminal, ChevronDown, ChevronUp,
  ListChecks, MessageSquare, AlertTriangle, ShieldAlert, FileQuestion,
  DollarSign, Award, Calendar, User, FileText, CheckCircle, Info, ShieldCheck
} from 'lucide-react';
import SummaryCard from '../components/SummaryCard';
import DiscrepancyTable from '../components/DiscrepancyTable';
import ExportButton from '../components/ExportButton';
import AuditLogConsole from '../components/AuditLogConsole';
import DisputeLetterModal from '../components/DisputeLetterModal';
import ContractQADrawer from '../components/ContractQADrawer';
import AuditDocumentPanel from '../components/AuditDocumentPanel';
import { getAuditLogs, submitFindingFeedback } from '../api';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Card from '../components/ui/Card';
import Modal from '../components/ui/Modal';

export default function AuditReport({ report, onBack }) {
  const [logs, setLogs] = useState([]);
  const [showLogs, setShowLogs] = useState(false);
  const [isDisputeModalOpen, setIsDisputeModalOpen] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [selectedRule, setSelectedRule] = useState(null);

  // Collapsible section states (collapsed by default)
  const [showRecoveryPlan, setShowRecoveryPlan] = useState(false);
  const [showComplianceFlags, setShowComplianceFlags] = useState(false);

  // v4: Learning Loop & Flags Review State
  const [resolvedFlags, setResolvedFlags] = useState({});
  const [activeReviewIdx, setActiveReviewIdx] = useState(null);
  const [flagNotes, setFlagNotes] = useState({});
  const [submittingFlagIdx, setSubmittingFlagIdx] = useState(null);

  const associatedFinding = useMemo(() => {
    if (!report?.review_flags) return {};
    const mapping = {};
    const allFindings = [
      ...(report.discrepancies || []),
      ...(report.missing_credits || []),
      ...(report.price_drifts || [])
    ];

    report.review_flags.forEach((flag, idx) => {
      const match = allFindings.find(f =>
        (flag.rule_id && f.rule_id === flag.rule_id) ||
        (flag.line_id && f.line_id === flag.line_id)
      );
      if (match) {
        mapping[idx] = match.finding_id;
      } else {
        mapping[idx] = flag.rule_id || flag.line_id || `flag_${idx}`;
      }
    });
    return mapping;
  }, [report]);

  const handleResolveFlag = async (idx, verdict) => {
    if (!report?.audit_id) return;
    const findingId = associatedFinding[idx];
    const notes = flagNotes[idx] || '';

    setSubmittingFlagIdx(idx);
    try {
      await submitFindingFeedback(report.audit_id, findingId, {
        verdict: verdict,
        reason: notes,
        reviewed_by: 'human_reviewer'
      });
      setResolvedFlags(prev => ({
        ...prev,
        [idx]: { verdict, reason: notes }
      }));
      setActiveReviewIdx(null);
    } catch (err) {
      console.error("Failed to submit finding feedback:", err);
      alert("Error submitting audit verdict: " + err.message);
    } finally {
      setSubmittingFlagIdx(null);
    }
  };

  const handleRuleClick = (ruleId) => {
    if (report?.rulebook?.rules) {
      const rule = report.rulebook.rules.find((r) => r.rule_id === ruleId);
      if (rule) {
        setSelectedRule(rule);
      }
    }
  };

  useEffect(() => {
    if (report?.audit_id) {
      getAuditLogs(report.audit_id).then(setLogs).catch(err => console.error('Failed to load audit logs:', err));
    }
  }, [report]);

  const typeLabels = {
    overcharge: 'Direct Overcharge',
    missed_discount: 'Unapplied Discount',
    unapplied_penalty: 'Unapplied SLA Penalty',
    incorrect_rate: 'Rate Sheet Mismatch',
    missing_credit: 'Unapplied Volume Credit',
    period_mismatch: 'Billing Cycle Mismatch',
    other: 'General Compliance Discrepancy'
  };

  const leakageByType = useMemo(() => {
    if (!report?.discrepancies) return {};
    const acc = {};
    report.discrepancies.forEach(d => {
      const rawType = d.discrepancy_type || 'other';
      const absDelta = Math.abs(parseFloat(d.delta || 0));
      if (!acc[rawType]) {
        acc[rawType] = { count: 0, total: 0 };
      }
      acc[rawType].count += 1;
      acc[rawType].total += absDelta;
    });
    return acc;
  }, [report?.discrepancies]);

  const sortedLeakageTypes = useMemo(() => {
    return Object.entries(leakageByType)
      .map(([type, data]) => ({
        type,
        label: typeLabels[type] || type.replace(/_/g, ' '),
        count: data.count,
        total: data.total,
      }))
      .sort((a, b) => b.total - a.total);
  }, [leakageByType]);

  const maxTypeLeakage = useMemo(() => {
    if (sortedLeakageTypes.length === 0) return 1;
    return Math.max(...sortedLeakageTypes.map(t => t.total));
  }, [sortedLeakageTypes]);

  const topDiscrepancies = useMemo(() => {
    if (!report?.discrepancies) return [];
    return [...report.discrepancies]
      .sort((a, b) => Math.abs(parseFloat(b.delta || 0)) - Math.abs(parseFloat(a.delta || 0)))
      .slice(0, 3);
  }, [report?.discrepancies]);

  const chunkedDiscrepancies = useMemo(() => {
    if (!report?.discrepancies) return [];
    const chunks = [];
    const chunkSize = 4; // fit exactly 4 detailed findings per page to stay spacious
    for (let i = 0; i < report.discrepancies.length; i += chunkSize) {
      chunks.push(report.discrepancies.slice(i, i + chunkSize));
    }
    return chunks;
  }, [report?.discrepancies]);

  const leakageVal = Math.abs(parseFloat(report?.summary?.total_leakage || 0));
  const totalAuditedLines = report?.summary?.total_lines_audited || 0;
  const compliantLinesCount = report?.summary?.compliant_lines || 0;
  const complianceScore = report?.summary?.compliance_score || (totalAuditedLines ? Math.round((compliantLinesCount / totalAuditedLines) * 100) : 100);

  if (!report) return null;

  // Total pages calculation: Cover Page (1) + Financial Summary (1) + Findings Ledger chunks + Action/Sign-off Page (1)
  const totalReportPages = 3 + (chunkedDiscrepancies.length || 1);

  return (
    <div id="audit-report-content" className="space-y-6 print:py-0">

      {/* ── Screen Header ── */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4 border-b border-slate-200 pb-6 print:hidden">
        <div>
          <button type="button" onClick={onBack} className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-900 mb-3 transition-colors">
            <ArrowLeft className="h-4 w-4 stroke-[1.5]" /> Back to History
          </button>
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl font-display font-bold text-slate-900">Supplier Audit Report</h1>
            <Badge variant="success" className="flex items-center gap-1"><FileCheck className="h-3.5 w-3.5 stroke-[1.5]" /> Verified</Badge>
          </div>
          <p className="text-slate-500 text-xs mt-1.5">
            Ref: <span className="font-mono">{report.audit_id}</span> · {new Date(report.report_generated_at).toLocaleString()}
          </p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <Button variant="secondary" size="sm" className="flex items-center gap-1.5" onClick={() => setIsChatOpen(true)}>
            <MessageSquare className="h-4 w-4 stroke-[1.5]" /> Ask About Contract
          </Button>
          <ExportButton report={report} />
        </div>
      </div>

      <DisputeLetterModal isOpen={isDisputeModalOpen} onClose={() => setIsDisputeModalOpen(false)} auditId={report.audit_id} supplierName={report.summary?.supplier_name || ''} />

      {/* ── Screen-Only Interactive Layout ── */}
      <div className="print:hidden space-y-6">
        <SummaryCard summary={report.summary} discrepancies={report.discrepancies} onGenerateDispute={() => setIsDisputeModalOpen(true)}>
          {report.compliant_lines?.length > 0 && report.discrepancies.length === 0 && (
            <Card className="text-center bg-emerald-50 border-emerald-200 max-w-xl mx-auto p-6">
              <ListChecks className="h-8 w-8 text-emerald-600 mx-auto mb-3 stroke-[1.5]" />
              <h4 className="text-base font-semibold text-slate-900">All Line Charges Compliant</h4>
              <p className="text-sm text-slate-600 mt-2">No overcharges or SLA penalties were flagged.</p>
            </Card>
          )}

          {report.discrepancies?.length > 0 && <DiscrepancyTable discrepancies={report.discrepancies} />}
        </SummaryCard>

        {(report.review_flags?.length > 0 || report.data_required_flags?.length > 0 || report.rules_never_billed?.length > 0) && (
          <Card className="border-slate-200 bg-slate-50/50 shadow-sm">
            <button
              type="button"
              onClick={() => setShowComplianceFlags(!showComplianceFlags)}
              className="w-full flex items-center justify-between font-semibold text-slate-900 focus:outline-none"
            >
              <div className="flex items-center gap-2">
                <ShieldAlert className="h-5 w-5 text-orange-500 stroke-[1.5]" />
                <span className="text-sm font-bold font-display">Audit Integrity &amp; Compliance Flags (v4)</span>
                <Badge variant="warning">{(report.review_flags?.length || 0) + (report.data_required_flags?.length || 0)} Total Flags</Badge>
              </div>
              {showComplianceFlags ? (
                <ChevronUp className="h-4 w-4 text-slate-400 stroke-[1.5]" />
              ) : (
                <ChevronDown className="h-4 w-4 text-slate-400 stroke-[1.5]" />
              )}
            </button>

            {showComplianceFlags && (
              <div className="mt-5 pt-5 border-t border-slate-200 grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Left Column: Needs Human Review (Interactive Feedback Loop) */}
              <div>
                <h4 className="text-xs font-bold text-orange-800 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                  <AlertTriangle className="h-4 w-4 stroke-[1.5] text-orange-600" />
                  Human Review &amp; Verdict Loop
                </h4>
                <div className="space-y-3">
                  {report.review_flags?.length > 0 ? (
                    report.review_flags.map((flag, i) => {
                      const isResolved = resolvedFlags[i] !== undefined;
                      const resolution = resolvedFlags[i];
                      const isEditing = activeReviewIdx === i;

                      return (
                        <div
                          key={i}
                          className={`transition-all duration-200 bg-white p-4 rounded-xl border shadow-sm ${isResolved
                              ? resolution.verdict === 'CORRECT'
                                ? 'border-emerald-200 bg-emerald-50/10'
                                : 'border-slate-200 bg-slate-50/30 text-slate-500'
                              : isEditing
                                ? 'border-orange-400 ring-2 ring-orange-100'
                                : 'border-orange-100 hover:border-orange-300 hover:shadow-md'
                            }`}
                        >
                          <div className="flex justify-between items-start gap-2">
                            <div>
                              <p className="font-semibold text-slate-800 text-sm flex items-center gap-1.5">
                                {flag.rule_id || flag.line_id || 'Audit Item'}
                                {!isResolved && (
                                  <span className="flex h-2 w-2 relative">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-2 w-2 bg-orange-500"></span>
                                  </span>
                                )}
                              </p>
                              <p className="text-slate-500 text-xs mt-0.5">{flag.reason}</p>
                            </div>

                            {isResolved && (
                              <Badge variant={resolution.verdict === 'CORRECT' ? 'success' : 'secondary'} className="text-[10px]">
                                {resolution.verdict === 'CORRECT' ? 'Confirmed Finding' : 'False Positive'}
                              </Badge>
                            )}
                          </div>

                          {flag.clause_text && (
                            <div className="mt-2.5 bg-slate-50 p-2.5 rounded border border-slate-100 font-mono text-[10px] text-slate-600 line-clamp-3 italic">
                              &ldquo;{flag.clause_text}&rdquo;
                            </div>
                          )}

                          {/* Expanded Form to Submit Feedback */}
                          {!isResolved && isEditing && (
                            <div className="mt-4 pt-3 border-t border-slate-100 space-y-3">
                              <div>
                                <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1 font-sans">Reviewer Justification</label>
                                <textarea
                                  placeholder="Provide context for this decision..."
                                  value={flagNotes[i] || ''}
                                  onChange={(e) => setFlagNotes(prev => ({ ...prev, [i]: e.target.value }))}
                                  className="w-full text-xs border border-slate-200 rounded-lg p-2 focus:ring-1 focus:ring-orange-500 focus:border-orange-500 outline-none"
                                  rows={2}
                                />
                              </div>
                              <div className="flex justify-end gap-2 text-xs">
                                <Button
                                  variant="secondary"
                                  size="xs"
                                  onClick={() => setActiveReviewIdx(null)}
                                  disabled={submittingFlagIdx === i}
                                >
                                  Cancel
                                </Button>
                                <Button
                                  variant="secondary"
                                  size="xs"
                                  onClick={() => handleResolveFlag(i, 'FALSE_POSITIVE')}
                                  disabled={submittingFlagIdx === i}
                                  className="text-slate-600 border-slate-200 hover:bg-slate-100"
                                >
                                  {submittingFlagIdx === i ? 'Submitting...' : 'Dismiss Flag'}
                                </Button>
                                <Button
                                  variant="primary"
                                  size="xs"
                                  onClick={() => handleResolveFlag(i, 'CORRECT')}
                                  disabled={submittingFlagIdx === i}
                                  className="bg-emerald-600 hover:bg-emerald-700 text-white"
                                >
                                  {submittingFlagIdx === i ? 'Submitting...' : 'Confirm Dispute'}
                                </Button>
                              </div>
                            </div>
                          )}

                          {!isResolved && !isEditing && (
                            <div className="mt-3 flex justify-end">
                              <button
                                onClick={() => setActiveReviewIdx(i)}
                                className="text-xs font-semibold text-orange-600 hover:text-orange-700 bg-orange-50 px-2.5 py-1 rounded-md border border-orange-100 transition-colors"
                              >
                                Resolve Verdict
                              </button>
                            </div>
                          )}

                          {isResolved && resolution.reason && (
                            <div className="mt-2 text-xs bg-slate-50/50 p-2 rounded border border-slate-100 text-slate-500 italic">
                              <span className="font-bold font-sans not-italic text-slate-700 block text-[9px] uppercase tracking-wider mb-0.5">Reviewer Notes:</span>
                              &ldquo;{resolution.reason}&rdquo;
                            </div>
                          )}
                        </div>
                      );
                    })
                  ) : (
                    <div className="bg-white p-6 rounded-xl border border-dashed border-slate-200 text-center text-slate-500">
                      <ShieldCheck className="h-8 w-8 text-emerald-500 mx-auto mb-2 stroke-[1.5]" />
                      <p className="text-xs font-semibold text-slate-700">No human review flags outstanding.</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Right Column: Missing Data & Unused Contract Rules */}
              <div className="space-y-6">
                <div>
                  <h4 className="text-xs font-bold text-blue-800 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                    <FileQuestion className="h-4 w-4 stroke-[1.5] text-blue-600" />
                    Missing Support Data
                  </h4>
                  <div className="space-y-3">
                    {report.data_required_flags?.length > 0 ? (
                      report.data_required_flags.map((flag, i) => (
                        <div key={i} className="bg-white p-4 rounded-xl border border-blue-100 shadow-sm">
                          <p className="font-semibold text-slate-800 text-sm flex justify-between items-center">
                            <span>{flag.rule_id}</span>
                            <Badge variant="brand" className="text-[9px] font-mono">{flag.clause_section}</Badge>
                          </p>
                          <p className="text-slate-600 text-xs mt-1.5 leading-relaxed">{flag.reason}</p>
                        </div>
                      ))
                    ) : (
                      <div className="bg-white p-6 rounded-xl border border-dashed border-slate-200 text-center text-slate-500">
                        <CheckCircle className="h-8 w-8 text-emerald-500 mx-auto mb-2 stroke-[1.5]" />
                        <p className="text-xs font-semibold text-slate-700">No missing supporting details found.</p>
                      </div>
                    )}
                  </div>
                </div>

                {report.rules_never_billed?.length > 0 && (
                  <div className="border-t border-slate-200 pt-5">
                    <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">
                      Rules Never Triggered
                    </h4>
                    <p className="text-slate-500 text-xs mb-3">
                      The following pricing rules or SLAs were parsed from the contract but never billed on any invoice:
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {report.rules_never_billed.map((ruleId, i) => (
                        <button
                          key={i}
                          type="button"
                          onClick={() => handleRuleClick(ruleId)}
                          className="focus:outline-none transition-colors"
                        >
                          <Badge
                            variant="secondary"
                            className="bg-white border-slate-200 text-slate-600 hover:border-slate-400 hover:bg-slate-50 cursor-pointer text-xs"
                          >
                            {ruleId}
                          </Badge>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </Card>
      )}

        {report.recommendations?.length > 0 && (
          <Card className="border-slate-200 bg-white shadow-sm">
            <button
              type="button"
              onClick={() => setShowRecoveryPlan(!showRecoveryPlan)}
              className="w-full flex items-center justify-between font-semibold text-slate-900 focus:outline-none"
            >
              <div className="flex items-center gap-2">
                <ListChecks className="h-4 w-4 text-teal-600 stroke-[1.5]" />
                <span className="text-sm font-bold font-display">Recovery Plan</span>
                <Badge variant="brand">{report.recommendations.length} action{report.recommendations.length > 1 ? 's' : ''}</Badge>
              </div>
              {showRecoveryPlan ? (
                <ChevronUp className="h-4 w-4 text-slate-400 stroke-[1.5]" />
              ) : (
                <ChevronDown className="h-4 w-4 text-slate-400 stroke-[1.5]" />
              )}
            </button>

            {showRecoveryPlan && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-5 pt-5 border-t border-slate-100">
                {report.recommendations.map((rec, index) => (
                  <div key={index} className="flex items-start gap-3.5 bg-slate-50/50 p-4 rounded-xl border border-slate-200/80 shadow-sm hover:border-slate-300 transition-colors">
                    <span className="flex items-center justify-center h-6 w-6 rounded-full bg-teal-100 text-teal-700 text-xs font-bold shrink-0 shadow-sm">
                      {index + 1}
                    </span>
                    <p className="text-xs text-slate-700 leading-relaxed font-medium pt-0.5">{rec}</p>
                  </div>
                ))}
              </div>
            )}
          </Card>
        )}

        <AuditDocumentPanel auditId={report.audit_id} discrepancies={report.discrepancies || []} />

        <Card className="print:hidden">
          <button type="button" onClick={() => setShowLogs(!showLogs)} className="w-full flex items-center justify-between font-semibold text-slate-900 focus:outline-none">
            <div className="flex items-center gap-2">
              <Terminal className="h-4 w-4 text-teal-600 stroke-[1.5]" />
              <span className="text-sm">Agent Audit Trail</span>
              <Badge variant="default">{logs.length} events</Badge>
            </div>
            {showLogs ? <ChevronUp className="h-4 w-4 text-slate-400 stroke-[1.5]" /> : <ChevronDown className="h-4 w-4 text-slate-400 stroke-[1.5]" />}
          </button>
          {showLogs && <div className="mt-4"><AuditLogConsole logs={logs} /></div>}
        </Card>
      </div>

      {/* ── Executive Print-Only Report Layout (CEO/CFO Ready) ── */}
      <div className="hidden print:block w-[800px] mx-auto text-slate-800 bg-white leading-normal font-sans text-xs">

        {/* PAGE 1: TITLE PAGE & EXECUTIVE SCORECARD */}
        <div className="w-[800px] h-[1131px] p-12 bg-white flex flex-col justify-between border-b border-slate-100" style={{ boxSizing: 'border-box' }}>
          <div>
            {/* Header branding */}
            <div className="flex justify-between items-center border-b-2 border-slate-900 pb-4">
              <div className="flex items-center gap-2">
                <div className="h-6 w-6 rounded bg-teal-600 flex items-center justify-center text-white font-extrabold text-sm">P</div>
                <span className="text-sm font-extrabold text-slate-900 uppercase tracking-wider font-display">ProcureAI</span>
              </div>
              <span className="text-[10px] font-bold text-rose-600 tracking-widest uppercase bg-rose-50 px-2 py-0.5 rounded border border-rose-200">CONFIDENTIAL · EXECUTIVE BRIEFING</span>
            </div>

            {/* Document Title */}
            <div className="my-10 space-y-2">
              <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight leading-tight">
                SUPPLIER COMPLIANCE &amp;<br />
                FINANCIAL LEAKAGE AUDIT
              </h1>
              <p className="text-sm text-slate-500 font-medium">
                Comprehensive automated verification of billing compliance against active contractual terms.
              </p>
            </div>

            {/* Document Particulars Grid */}
            <div className="grid grid-cols-2 gap-6 bg-slate-50 p-5 rounded-xl border border-slate-200 mb-8">
              <div className="space-y-2.5">
                <div>
                  <span className="text-[9px] uppercase font-bold text-slate-400 block tracking-wider">AUDIT SUBJECT</span>
                  <span className="text-xs font-bold text-slate-800">{report.summary?.supplier_name}</span>
                </div>
                <div>
                  <span className="text-[9px] uppercase font-bold text-slate-400 block tracking-wider">CONTRACT ID</span>
                  <span className="text-xs font-mono font-semibold text-slate-700">{report.summary?.contract_id}</span>
                </div>
                <div>
                  <span className="text-[9px] uppercase font-bold text-slate-400 block tracking-wider">BILLING CYCLE AUDITED</span>
                  <span className="text-xs font-bold text-slate-800">{report.summary?.billing_period}</span>
                </div>
              </div>
              <div className="space-y-2.5">
                <div>
                  <span className="text-[9px] uppercase font-bold text-slate-400 block tracking-wider">AUDIT GENERATION DATE</span>
                  <span className="text-xs font-bold text-slate-800">{new Date(report.report_generated_at).toLocaleString()}</span>
                </div>
                <div>
                  <span className="text-[9px] uppercase font-bold text-slate-400 block tracking-wider">REPORT REFERENCE ID</span>
                  <span className="text-xs font-mono font-semibold text-slate-700">{report.audit_id}</span>
                </div>
                <div>
                  <span className="text-[9px] uppercase font-bold text-slate-400 block tracking-wider">VERIFICATION STATUS</span>
                  <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    <FileCheck className="h-3 w-3 stroke-[1.5]" /> CRITIC-VERIFIED
                  </span>
                </div>
              </div>
            </div>

            {/* Financial Highlights Dashboard Section */}
            <div className="space-y-4 mb-8">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Financial Compliance Dashboard</h3>
              <div className="grid grid-cols-3 gap-4">
                <div className="border border-rose-200 rounded-xl p-4 bg-rose-50/20 relative overflow-hidden flex flex-col justify-between min-h-[120px]">
                  <div>
                    <span className="text-[9px] font-bold text-rose-800 uppercase tracking-wider block">Recoverable Leakage</span>
                    <p className="text-2xl font-black font-mono text-rose-700 mt-1">
                      -${leakageVal.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </p>
                  </div>
                  <div className="border-t border-rose-200/50 pt-2 mt-2 flex justify-between text-[9px] font-semibold text-rose-800">
                    <span>Severity Events:</span>
                    <span>{report.summary?.critical_count || 0} Crit · {report.summary?.high_count || 0} High</span>
                  </div>
                </div>

                <div className="border border-emerald-200 rounded-xl p-4 bg-emerald-50/10 flex flex-col justify-between min-h-[120px]">
                  <div>
                    <span className="text-[9px] font-bold text-emerald-800 uppercase tracking-wider block">Compliance Score</span>
                    <p className="text-2xl font-black font-mono text-emerald-700 mt-1">
                      {complianceScore}%
                    </p>
                    {/* Visual custom progress bar */}
                    <div className="w-full bg-slate-200 h-1.5 rounded-full mt-2 overflow-hidden">
                      <div
                        className={`h-full rounded-full ${complianceScore >= 95 ? 'bg-emerald-600' : complianceScore >= 80 ? 'bg-amber-500' : 'bg-rose-600'}`}
                        style={{ width: `${complianceScore}%` }}
                      />
                    </div>
                  </div>
                  <span className={`text-[9px] font-bold uppercase tracking-wider ${complianceScore >= 95 ? 'text-emerald-700' : complianceScore >= 80 ? 'text-amber-700' : 'text-rose-700'}`}>
                    {complianceScore >= 95 ? 'OPTIMAL SAFEGUARD' : complianceScore >= 80 ? 'ACTION RECOMMENDED' : 'CRITICAL RISK EXPOSURE'}
                  </span>
                </div>

                <div className="border border-slate-200 rounded-xl p-4 bg-white flex flex-col justify-between min-h-[120px]">
                  <div>
                    <span className="text-[9px] font-bold text-slate-500 uppercase tracking-wider block">Verification Coverage</span>
                    <p className="text-xl font-bold font-mono text-slate-800 mt-1">
                      {compliantLinesCount} / {totalAuditedLines}
                    </p>
                    <span className="text-[9px] text-slate-400 block mt-1">Invoice charge items audited</span>
                  </div>
                  <span className="text-[9px] font-semibold text-slate-400 uppercase tracking-wider">
                    Discrepancy count: {report.summary?.discrepancy_count || 0}
                  </span>
                </div>
              </div>
            </div>

            {/* Executive summary statement */}
            {report.summary?.executive_summary && (
              <div className="bg-slate-50 border-l-4 border-teal-500 p-5 rounded-r-xl">
                <h4 className="text-xs font-bold text-teal-800 uppercase tracking-wider flex items-center gap-1 mb-2">
                  <Award className="h-4 w-4 stroke-[1.5]" />
                  EXECUTIVE SUMMARY MEMORANDUM (C-SUITE DIRECTIVE)
                </h4>
                <p className="text-xs text-slate-700 italic leading-relaxed">
                  &ldquo;{report.summary.executive_summary}&rdquo;
                </p>
              </div>
            )}
          </div>

          {/* Page Footer */}
          <div className="flex justify-between items-center border-t border-slate-100 pt-3 text-[10px] text-slate-400 font-mono">
            <span>PROCUREAI SYSTEM AUDIT LOG</span>
            <span>Page 1 of {totalReportPages}</span>
          </div>
        </div>

        <div className="print-page-break" />

        {/* PAGE 2: FINANCIAL RECONCILIATION & LEAKAGE ATTRIBUTION */}
        <div className="w-[800px] h-[1131px] p-12 bg-white flex flex-col justify-between border-b border-slate-100" style={{ boxSizing: 'border-box' }}>
          <div>
            {/* Header */}
            <div className="flex justify-between items-center border-b border-slate-200 pb-3 mb-6">
              <div>
                <h3 className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Section 1.0 — Financial Impact Analysis</h3>
                <h4 className="text-sm font-bold text-slate-800">Leakage Attribution &amp; High-Exposure Reconciliation</h4>
              </div>
              <span className="text-[10px] font-mono text-slate-400">Ref: {report.audit_id}</span>
            </div>

            <div className="space-y-6">
              {/* Attribution Table */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">Leakage Attribution by Category</h4>
                <table className="w-full text-left border border-slate-200 rounded-lg overflow-hidden">
                  <thead className="bg-slate-50 text-[10px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200">
                    <tr>
                      <th className="py-2.5 px-3">Discrepancy Category</th>
                      <th className="py-2.5 px-3 text-center w-24">Events Count</th>
                      <th className="py-2.5 px-3 text-right w-36">Total Leakage</th>
                      <th className="py-2.5 px-3 text-right w-24">Leakage %</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 text-xs">
                    {sortedLeakageTypes.map((item) => {
                      const pct = leakageVal > 0 ? (item.total / leakageVal) * 100 : 0;
                      return (
                        <tr key={item.type} className="hover:bg-slate-50">
                          <td className="py-2.5 px-3 font-semibold text-slate-700">{item.label}</td>
                          <td className="py-2.5 px-3 text-center font-semibold text-slate-600">{item.count}</td>
                          <td className="py-2.5 px-3 text-right font-mono font-bold text-rose-600">
                            -${item.total.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                          </td>
                          <td className="py-2.5 px-3 text-right font-mono font-semibold text-slate-500">
                            {pct.toFixed(1)}%
                          </td>
                        </tr>
                      );
                    })}
                    {sortedLeakageTypes.length === 0 && (
                      <tr>
                        <td colSpan="4" className="py-4 text-center text-slate-500 italic">No discrepancy categories recorded.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {/* Attribution Chart (Visual bar graph using pure CSS) */}
              {sortedLeakageTypes.length > 0 && (
                <div className="space-y-3 border border-slate-200 rounded-xl p-4 bg-slate-50/50">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600">Visual Leakage Distribution Map</h4>
                  <div className="space-y-3">
                    {sortedLeakageTypes.slice(0, 4).map((item) => {
                      const pct = leakageVal > 0 ? (item.total / leakageVal) * 100 : 0;
                      return (
                        <div key={item.type} className="space-y-1">
                          <div className="flex justify-between text-[10px] font-semibold text-slate-700">
                            <span>{item.label} ({item.count} events)</span>
                            <span className="font-mono text-rose-600 font-bold">
                              -${item.total.toLocaleString('en-US', { minimumFractionDigits: 2 })} ({pct.toFixed(1)}%)
                            </span>
                          </div>
                          <div className="w-full bg-slate-200 h-2.5 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-rose-500 to-amber-500 rounded-full"
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Top Exposure Items (Big ticket items CFO wants) */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">Top 3 Billing Discrepancies by Value</h4>
                <table className="w-full text-left border border-slate-200 rounded-lg overflow-hidden">
                  <thead className="bg-slate-50 text-[10px] font-bold text-slate-500 uppercase border-b border-slate-200">
                    <tr>
                      <th className="py-2 px-3">Invoice Ref</th>
                      <th className="py-2 px-3">Discrepancy Category</th>
                      <th className="py-2 px-3">Contractual Section</th>
                      <th className="py-2 px-3 text-right">Leakage Value</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 text-xs">
                    {topDiscrepancies.map((d, i) => (
                      <tr key={d.finding_id} className="hover:bg-slate-50">
                        <td className="py-2.5 px-3 font-semibold text-slate-800">
                          {d.invoice_id} <span className="text-[10px] font-mono text-slate-400 block font-normal">Line: {d.line_id}</span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-600 font-medium">{typeLabels[d.discrepancy_type] || d.discrepancy_type.replace(/_/g, ' ')}</td>
                        <td className="py-2.5 px-3 text-slate-500 font-mono text-[10px]">{d.clause_reference}</td>
                        <td className="py-2.5 px-3 text-right font-mono font-bold text-rose-600">
                          -${Math.abs(parseFloat(d.delta)).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                        </td>
                      </tr>
                    ))}
                    {topDiscrepancies.length === 0 && (
                      <tr>
                        <td colSpan="4" className="py-4 text-center text-slate-500 italic">No discrepancies mapped.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Page Footer */}
          <div className="flex justify-between items-center border-t border-slate-100 pt-3 text-[10px] text-slate-400 font-mono">
            <span>PROCUREAI FINANCIAL ANALYSIS</span>
            <span>Page 2 of {totalReportPages}</span>
          </div>
        </div>

        {/* PAGES 3 to 3+N: CHUNKED LEDGER TABLES */}
        {chunkedDiscrepancies.length === 0 ? (
          <>
            <div className="print-page-break" />
            <div className="w-[800px] h-[1131px] p-12 bg-white flex flex-col justify-between border-b border-slate-100" style={{ boxSizing: 'border-box' }}>
              <div>
                <div className="flex justify-between items-center border-b border-slate-200 pb-3 mb-6">
                  <div>
                    <h3 className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Section 2.0 — Findings Ledger</h3>
                    <h4 className="text-sm font-bold text-slate-800">Compliance Audit Ledger &amp; Evidence</h4>
                  </div>
                  <span className="text-[10px] font-mono text-slate-400">Ref: {report.audit_id}</span>
                </div>
                <div className="flex flex-col items-center justify-center py-20 text-slate-400 space-y-2 border border-dashed border-slate-200 rounded-xl">
                  <CheckCircle className="h-10 w-10 text-emerald-500 stroke-[1.5]" />
                  <p className="font-semibold text-slate-700">All Charges 100% Compliant</p>
                  <p className="text-[10px] text-slate-500">Zero overcharges or SLA penalty omissions were identified in the audited lines.</p>
                </div>
              </div>
              <div className="flex justify-between items-center border-t border-slate-100 pt-3 text-[10px] text-slate-400 font-mono">
                <span>PROCUREAI LEDGER</span>
                <span>Page 3 of 4</span>
              </div>
            </div>
          </>
        ) : (
          chunkedDiscrepancies.map((chunk, chunkIdx) => {
            const pageNum = 3 + chunkIdx;
            return (
              <div key={chunkIdx} style={{ boxSizing: 'border-box' }}>
                <div className="print-page-break" />
                <div className="w-[800px] h-[1131px] p-12 bg-white flex flex-col justify-between border-b border-slate-100">
                  <div>
                    {/* Header */}
                    <div className="flex justify-between items-center border-b border-slate-200 pb-3">
                      <div>
                        <h3 className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Section 2.0 — Findings Ledger</h3>
                        <h4 className="text-sm font-bold text-slate-800">Compliance Audit Ledger &amp; Evidence (Part {chunkIdx + 1} of {chunkedDiscrepancies.length})</h4>
                      </div>
                      <span className="text-[10px] font-mono text-slate-400">Ref: {report.audit_id}</span>
                    </div>

                    {/* Ledger Table */}
                    <div className="py-6">
                      <table className="w-full text-left border-collapse">
                        <thead>
                          <tr className="border-b border-slate-200 text-[9px] font-bold uppercase text-slate-400">
                            <th className="pb-2 w-[120px]">Ref / Severity</th>
                            <th className="pb-2 w-[130px]">Discrepancy Category</th>
                            <th className="pb-2">Details &amp; Contractual Proof</th>
                            <th className="pb-2 text-right w-[130px]">Expected vs Charged</th>
                            <th className="pb-2 text-right w-[90px]">Leakage</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {chunk.map((d) => (
                            <tr key={d.finding_id} className="text-xs">
                              <td className="py-3.5 pr-2 align-top">
                                <span className="font-bold text-slate-900 block">{d.invoice_id}</span>
                                <span className="text-[9px] text-slate-500 block font-mono">Line ID: {d.line_id}</span>
                                <span className={`inline-block mt-1 px-1.5 py-0.5 rounded text-[8px] font-bold ${d.severity === 'CRITICAL' ? 'bg-rose-50 text-rose-700 border border-rose-100' :
                                    d.severity === 'HIGH' ? 'bg-amber-50 text-amber-700 border border-amber-100' :
                                      'bg-sky-50 text-sky-700 border border-sky-100'
                                  }`}>
                                  {d.severity}
                                </span>
                              </td>
                              <td className="py-3.5 pr-2 align-top font-semibold text-slate-700 text-[11px]">
                                {typeLabels[d.discrepancy_type] || d.discrepancy_type.replace(/_/g, ' ')}
                              </td>
                              <td className="py-3.5 pr-2 align-top space-y-1.5">
                                <p className="text-slate-700 font-medium leading-relaxed">{d.description}</p>
                                {d.clause_text && (
                                  <div className="bg-slate-50 p-2.5 rounded-lg border-l-2 border-teal-500 font-mono text-[9px] text-slate-600 leading-normal">
                                    <span className="font-bold text-teal-800 block text-[8px] uppercase tracking-wider mb-0.5">Clause: {d.clause_reference}</span>
                                    &ldquo;{d.clause_text}&rdquo;
                                  </div>
                                )}
                              </td>
                              <td className="py-3.5 pr-2 align-top text-right font-mono text-slate-600">
                                <div className="text-[10px]"><span className="text-slate-400">Exp:</span> <span className="text-emerald-600 font-bold">${parseFloat(d.unit_price_expected).toFixed(2)}</span></div>
                                <div className="text-[10px]"><span className="text-slate-400">Chg:</span> <span className="text-rose-600 font-bold">${parseFloat(d.unit_price_charged).toFixed(2)}</span></div>
                              </td>
                              <td className="py-3.5 align-top text-right font-mono font-bold text-rose-600">
                                -${Math.abs(parseFloat(d.delta)).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Page Footer */}
                  <div className="flex justify-between items-center border-t border-slate-100 pt-3 text-[10px] text-slate-400 font-mono">
                    <span>PROCUREAI LEDGER</span>
                    <span>Page {pageNum} of {totalReportPages}</span>
                  </div>
                </div>
              </div>
            );
          })
        )}

        <div className="print-page-break" />

        {/* FINAL PAGE: RISK CONTROL, STRATEGIC NEXT STEPS & SIGN-OFF */}
        <div className="w-[800px] h-[1131px] p-12 bg-white flex flex-col justify-between border border-slate-200" style={{ boxSizing: 'border-box' }}>
          <div>
            {/* Header */}
            <div className="flex justify-between items-center border-b border-slate-200 pb-3 mb-6">
              <div>
                <h3 className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Section 3.0 — Risk Control &amp; Recovery Roadmap</h3>
                <h4 className="text-sm font-bold text-slate-800">Governance Integrity &amp; Strategic Remediation</h4>
              </div>
              <span className="text-[10px] font-mono text-slate-400">Ref: {report.audit_id}</span>
            </div>

            <div className="space-y-6">
              {/* Audit Integrity Flags */}
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-3">
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                  <ShieldAlert className="h-4 w-4 text-amber-500 stroke-[1.5]" />
                  Audit Integrity &amp; Verification Status
                </h4>
                <p className="text-[11px] text-slate-600 leading-normal">
                  Integrity flags highlight areas requiring human verification or additional support data before launching disputes.
                </p>
                <div className="grid grid-cols-2 gap-4 pt-1">
                  <div className="space-y-2">
                    <h5 className="text-[10px] font-bold text-amber-800 uppercase tracking-wider">Needs Human Review ({report.review_flags?.length || 0})</h5>
                    {report.review_flags?.length > 0 ? (
                      <ul className="space-y-1.5 max-h-[120px] overflow-y-auto pr-1">
                        {report.review_flags.slice(0, 3).map((flag, idx) => (
                          <li key={idx} className="text-[10px] text-slate-600 bg-white p-2 rounded border border-slate-200 font-medium">
                            <span className="font-bold text-slate-800">{flag.rule_id || flag.line_id || 'Item'}:</span> {flag.reason}
                          </li>
                        ))}
                        {report.review_flags.length > 3 && (
                          <li className="text-[9px] text-slate-400 italic font-mono text-center">
                            + {report.review_flags.length - 3} more review flag(s)
                          </li>
                        )}
                      </ul>
                    ) : (
                      <p className="text-[10px] text-emerald-700 bg-emerald-50 p-2.5 rounded border border-emerald-100 font-medium">
                        No manual review flags generated.
                      </p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <h5 className="text-[10px] font-bold text-blue-800 uppercase tracking-wider">Missing Support Data ({report.data_required_flags?.length || 0})</h5>
                    {report.data_required_flags?.length > 0 ? (
                      <ul className="space-y-1.5 max-h-[120px] overflow-y-auto pr-1">
                        {report.data_required_flags.slice(0, 3).map((flag, idx) => (
                          <li key={idx} className="text-[10px] text-slate-600 bg-white p-2 rounded border border-slate-200 font-medium">
                            <span className="font-bold text-slate-800">{flag.rule_id}:</span> {flag.reason}
                          </li>
                        ))}
                        {report.data_required_flags.length > 3 && (
                          <li className="text-[9px] text-slate-400 italic font-mono text-center">
                            + {report.data_required_flags.length - 3} more flag(s)
                          </li>
                        )}
                      </ul>
                    ) : (
                      <p className="text-[10px] text-emerald-700 bg-emerald-50 p-2.5 rounded border border-emerald-100 font-medium">
                        No missing support data flags generated.
                      </p>
                    )}
                  </div>
                </div>
              </div>

              {/* Rules Never Billed */}
              {report.rules_never_billed?.length > 0 && (
                <div className="border border-slate-200 rounded-xl p-4 space-y-2">
                  <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Contractual Safeguards (Rules Unused)</h4>
                  <p className="text-[10px] text-slate-600">
                    The following pricing rules and SLA templates did not result in billing operations or penalty triggers during this billing cycle:
                  </p>
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {report.rules_never_billed.map((ruleId, i) => (
                      <span key={i} className="px-2.5 py-1 bg-slate-100 text-slate-700 border border-slate-200 rounded font-mono text-[9px]">
                        {ruleId}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Strategic Recovery Action Plan */}
              <div className="border border-slate-200 rounded-xl p-4 space-y-3">
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                  <ListChecks className="h-4 w-4 text-teal-600 stroke-[1.5]" />
                  Strategic Recovery Action Plan
                </h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex gap-2.5 items-start">
                    <span className="flex items-center justify-center h-5 w-5 rounded-full bg-teal-100 text-teal-800 font-bold text-[9px] shrink-0">1</span>
                    <div>
                      <h5 className="text-[10px] font-bold text-slate-800">Formal Dispute Initiation</h5>
                      <p className="text-[9px] text-slate-500 leading-relaxed">Submit the formal dispute package detailing the flagged discrepancies to the supplier billing desk within 15 days.</p>
                    </div>
                  </div>
                  <div className="flex gap-2.5 items-start">
                    <span className="flex items-center justify-center h-5 w-5 rounded-full bg-teal-100 text-teal-800 font-bold text-[9px] shrink-0">2</span>
                    <div>
                      <h5 className="text-[10px] font-bold text-slate-800">Invoice Hold Adjustment</h5>
                      <p className="text-[9px] text-slate-500 leading-relaxed">Where contract clauses permit, withhold the disputed leakage sum of <strong>${leakageVal.toLocaleString('en-US', { minimumFractionDigits: 2 })}</strong> from outstanding payables.</p>
                    </div>
                  </div>
                  <div className="flex gap-2.5 items-start">
                    <span className="flex items-center justify-center h-5 w-5 rounded-full bg-teal-100 text-teal-800 font-bold text-[9px] shrink-0">3</span>
                    <div>
                      <h5 className="text-[10px] font-bold text-slate-800">Supplier Audit Alignment</h5>
                      <p className="text-[9px] text-slate-500 leading-relaxed">Convene a joint billing reconciliation workshop with the supplier's CFO and account management team.</p>
                    </div>
                  </div>
                  <div className="flex gap-2.5 items-start">
                    <span className="flex items-center justify-center h-5 w-5 rounded-full bg-teal-100 text-teal-800 font-bold text-[9px] shrink-0">4</span>
                    <div>
                      <h5 className="text-[10px] font-bold text-slate-800">Historical Lookback Sweep</h5>
                      <p className="text-[9px] text-slate-500 leading-relaxed">Initiate a compliance lookback sweep covering the prior 12 to 24 months of invoice histories to isolate recurring leaks.</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* C-Suite Sign-off Panel */}
              <div className="border border-slate-200 rounded-xl p-4 bg-slate-50/50 space-y-3">
                <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-wider text-center">Executive Approvals &amp; Sign-off Block</h4>
                <div className="grid grid-cols-3 gap-6 pt-2">
                  <div className="border-t border-slate-300 pt-2 text-center space-y-1">
                    <p className="text-[10px] font-bold text-slate-700">Internal Audit Lead</p>
                    <p className="text-[9px] text-slate-400 italic">ProcureAI Compliance System</p>
                    <div className="h-6 flex items-center justify-center text-[9px] text-emerald-600 font-bold uppercase tracking-wider">
                      [ Critic Verified ]
                    </div>
                  </div>
                  <div className="border-t border-slate-300 pt-2 text-center space-y-1">
                    <p className="text-[10px] font-bold text-slate-700">Chief Financial Officer (CFO)</p>
                    <p className="text-[9px] text-slate-400">Date: __________________</p>
                    <div className="h-6 border-b border-dashed border-slate-300 mx-4"></div>
                  </div>
                  <div className="border-t border-slate-300 pt-2 text-center space-y-1">
                    <p className="text-[10px] font-bold text-slate-700">Chief Executive Officer (CEO)</p>
                    <p className="text-[9px] text-slate-400">Date: __________________</p>
                    <div className="h-6 border-b border-dashed border-slate-300 mx-4"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Page Footer */}
          <div className="flex justify-between items-center border-t border-slate-100 pt-3 text-[10px] text-slate-400 font-mono">
            <span>PROCUREAI GOVERNANCE BRIEFING</span>
            <span>Page {totalReportPages} of {totalReportPages}</span>
          </div>
        </div>
      </div>

      <ContractQADrawer isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} auditId={report.audit_id} supplierName={report.summary?.supplier_name || ''} />

      <Modal isOpen={!!selectedRule} onClose={() => setSelectedRule(null)} title={`Rule Details: ${selectedRule?.rule_id || ''}`}>
        {selectedRule && (
          <div className="space-y-4">
            <div>
              <h4 className="text-sm font-semibold text-slate-900">Description</h4>
              <p className="text-sm text-slate-700">{selectedRule.description}</p>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-slate-900">Type</h4>
              <Badge variant="secondary" className="mt-1 capitalize">{selectedRule.rule_type.replace(/_/g, ' ')}</Badge>
            </div>
            {selectedRule.clause_reference && (
              <div>
                <h4 className="text-sm font-semibold text-slate-900">Clause Reference</h4>
                <p className="text-sm text-slate-700">{selectedRule.clause_reference}</p>
              </div>
            )}
            {selectedRule.clause_text && (
              <div>
                <h4 className="text-sm font-semibold text-slate-900">Clause Text</h4>
                <p className="text-sm text-slate-700 bg-slate-50 p-3 rounded font-serif italic border-l-4 border-slate-300 mt-1">
                  {selectedRule.clause_text}
                </p>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}
