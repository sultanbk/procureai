/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Renders comparison grids between contract versions.
 * 
 * What it means:
 * Contract comparator page.
 * 
 * Importance in Project:
 * High. Allows users to trace changed clauses and terms.
 */

import { useState, useEffect } from 'react';
import {
  FileUp,
  FileText,
  X,
  AlertTriangle,
  Sparkles,
  FileCheck,
  ArrowRight,
  History,
  Loader2,
  Copy,
  Check,
} from 'lucide-react';
import { uploadForComparison, getComparison, getComparisonsList } from '../api';
import PageHeader from '../components/layout/PageHeader';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import { Table, TableHead, TableBody, TableRow, TableCell } from '../components/ui/Table';

export default function Compare() {
  const [oldFile, setOldFile] = useState(null);
  const [newFile, setNewFile] = useState(null);

  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState('');
  const [error, setError] = useState('');

  // Drag states
  const [dragOldActive, setDragOldActive] = useState(false);
  const [dragNewActive, setDragNewActive] = useState(false);

  // Results
  const [result, setResult] = useState(null);
  const [comparisonId, setComparisonId] = useState('');
  const [pastComparisons, setPastComparisons] = useState([]);
  const [copied, setCopied] = useState(false);

  const handleCopyNegotiationPoints = () => {
    if (!result || !result.negotiation_flags) return;
    const textToCopy = result.negotiation_flags.map((flag, idx) => `${idx + 1}. ${flag}`).join('\n');
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  // 'new' or 'history' unused tab removed

  useEffect(() => {
    fetchPastComparisons();
  }, []);

  async function fetchPastComparisons() {
    try {
      const list = await getComparisonsList();
      setPastComparisons(list);
    } catch (err) {
      console.error("Failed to load past comparisons", err);
      setError("Failed to load comparison history. Please check your connection.");
    }
  };

  const handleOldDrop = (e) => {
    e.preventDefault();
    setDragOldActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type === 'application/pdf') {
        setOldFile(file);
        setError('');
      } else {
        setError('Only PDF documents are supported for old contract version.');
      }
    }
  };

  const handleNewDrop = (e) => {
    e.preventDefault();
    setDragNewActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type === 'application/pdf') {
        setNewFile(file);
        setError('');
      } else {
        setError('Only PDF documents are supported for new contract version.');
      }
    }
  };

  const pollComparisonStatus = (id) => {
    let attempts = 0;
    let currentDelay = 2000;

    const poll = async () => {
      attempts++;
      if (attempts > 90) { // Timeout after ~90 attempts
        setIsLoading(false);
        setError('Comparison analysis timed out. Please try again.');
        return;
      }
      try {
        if (attempts < 5) {
          setProgress('Uploading and extracting text...');
        } else if (attempts < 15) {
          setProgress('Parsing old contract pricing rules...');
        } else if (attempts < 25) {
          setProgress('Parsing new contract pricing rules...');
        } else {
          setProgress('Diffing rules and generating CFO change summary...');
        }

        const data = await getComparison(id);
        if (data.status === 'COMPLETE' || data.overall_impact) {
          setResult(data);
          setIsLoading(false);
          fetchPastComparisons();
          return;
        } else if (data.status === 'FAILED') {
          setIsLoading(false);
          setError(data.error || 'Comparison extraction pipeline failed.');
          return;
        }
      } catch {
        // Poll through minor network glitches
      }

      // Exponential backoff up to 8 seconds max
      currentDelay = Math.min(currentDelay * 1.2, 8000);
      setTimeout(poll, currentDelay);
    };

    setTimeout(poll, currentDelay);
  };

  const handleCompare = async () => {
    if (!oldFile || !newFile) return;
    setIsLoading(true);
    setError('');
    setProgress('Uploading both contract versions...');

    try {
      const res = await uploadForComparison(oldFile, newFile);
      setComparisonId(res.comparison_id);
      pollComparisonStatus(res.comparison_id);
    } catch (err) {
      setIsLoading(false);
      setError(err.message || 'Failed to start comparison process');
    }
  };

  const loadPastResult = (cmp) => {
    if (cmp.status === 'COMPLETE' && cmp.diff_result) {
      setResult(cmp.diff_result);
      setComparisonId(cmp.id);
      setError('');
    } else {
      setComparisonId(cmp.id);
      setIsLoading(true);
      setError('');
      pollComparisonStatus(cmp.id);
    }
  };

  const resetComparator = () => {
    setOldFile(null);
    setNewFile(null);
    setResult(null);
    setComparisonId('');
    setError('');
  };

  const getImpactBadgeColor = (impact) => {
    switch (impact) {
      case 'BETTER':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'WORSE':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      case 'MIXED':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      default:
        return 'bg-slate-100 text-slate-600 border-slate-200';
    }
  };

  const getChangeTypeStyles = (changeType, impact) => {
    if (changeType === 'ADDED') {
      return {
        rowBg: 'bg-blue-50/60 border-l-4 border-l-blue-500',
        badge: 'bg-blue-50 text-blue-700 border-blue-200',
        badgeText: 'New Rule Added'
      };
    }
    if (changeType === 'REMOVED') {
      return {
        rowBg: 'bg-amber-50/60 border-l-4 border-l-amber-500',
        badge: 'bg-amber-50 text-amber-700 border-amber-200',
        badgeText: 'Rule Removed'
      };
    }

    // MODIFIED
    switch (impact) {
      case 'BETTER':
        return {
          rowBg: 'bg-emerald-50/60 border-l-4 border-l-emerald-500',
          badge: 'bg-emerald-50 text-emerald-700 border-emerald-200',
          badgeText: '↓ You pay less'
        };
      case 'WORSE':
        return {
          rowBg: 'bg-rose-50/60 border-l-4 border-l-rose-500',
          badge: 'bg-rose-50 text-rose-700 border-rose-200',
          badgeText: '↑ You pay more'
        };
      default:
        return {
          rowBg: 'bg-slate-50 border-l-4 border-l-slate-300',
          badge: 'bg-slate-100 text-slate-600 border-slate-200',
          badgeText: 'No financial change'
        };
    }
  };

  const dropzoneClass = (active) =>
    `border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all flex flex-col items-center justify-center min-h-[200px] ${
      active
        ? 'border-teal-500 bg-teal-50 shadow-sm'
        : 'border-slate-300 bg-slate-50 hover:border-slate-400 hover:bg-white'
    }`;

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      <PageHeader
        title="Contract Version Comparator"
        description="Upload any historical contract version alongside a revised agreement. Our system extracts pricing terms, runs an automated rule diff, and generates CFO negotiation talking points."
      >
        <div className="mt-4">
          <Badge variant="brand" className="inline-flex items-center gap-1.5 px-3 py-1">
            <Sparkles className="h-3.5 w-3.5" />
            Standalone Contract Analyzer
          </Badge>
        </div>
      </PageHeader>

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3 rounded-lg text-sm flex items-center gap-3 font-medium max-w-4xl mx-auto">
          <AlertTriangle className="h-5 w-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Container */}
      {!result && !isLoading && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Drag & Drop upload zones */}
          <Card className="lg:col-span-2 space-y-6">
            <h2 className="text-sm font-semibold text-slate-900 uppercase tracking-wide">Analyze Contract Versions</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Old Contract Version Upload */}
              <div className="space-y-3">
                <label className="text-xs font-semibold text-slate-600 uppercase tracking-wide block">1. Old Contract Version (Reference)</label>
                {!oldFile ? (
                  <div
                    onDragOver={e => { e.preventDefault(); setDragOldActive(true); }}
                    onDragLeave={() => setDragOldActive(false)}
                    onDrop={handleOldDrop}
                    className={dropzoneClass(dragOldActive)}
                    onClick={() => document.getElementById('old-contract-input').click()}
                  >
                    <input
                      id="old-contract-input"
                      type="file"
                      accept=".pdf"
                      className="hidden"
                      onChange={e => e.target.files?.[0] && setOldFile(e.target.files[0])}
                    />
                    <div className="p-3 bg-teal-50 rounded-lg text-teal-600 mb-3 border border-teal-100">
                      <FileUp className="h-6 w-6" />
                    </div>
                    <span className="text-sm font-semibold text-slate-900 block mb-1">Drag & drop old PDF here</span>
                    <span className="text-xs text-slate-500">or click to browse local files</span>
                  </div>
                ) : (
                  <div className="flex items-center justify-between p-4 bg-white border border-slate-200 rounded-lg shadow-sm min-h-[100px]">
                    <div className="flex items-center gap-3 truncate">
                      <div className="p-2.5 bg-emerald-50 text-emerald-600 rounded-lg border border-emerald-200">
                        <FileCheck className="h-5 w-5" />
                      </div>
                      <div className="truncate">
                        <span className="text-sm font-semibold text-slate-900 block truncate">{oldFile.name}</span>
                        <span className="text-xs text-slate-500 font-mono">{(oldFile.size / 1024 / 1024).toFixed(2)} MB</span>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setOldFile(null)}
                      className="text-slate-400 hover:text-rose-600"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                )}
              </div>

              {/* New Contract Version Upload */}
              <div className="space-y-3">
                <label className="text-xs font-semibold text-slate-600 uppercase tracking-wide block">2. New Contract Version (Proposed)</label>
                {!newFile ? (
                  <div
                    onDragOver={e => { e.preventDefault(); setDragNewActive(true); }}
                    onDragLeave={() => setDragNewActive(false)}
                    onDrop={handleNewDrop}
                    className={dropzoneClass(dragNewActive)}
                    onClick={() => document.getElementById('new-contract-input').click()}
                  >
                    <input
                      id="new-contract-input"
                      type="file"
                      accept=".pdf"
                      className="hidden"
                      onChange={e => e.target.files?.[0] && setNewFile(e.target.files[0])}
                    />
                    <div className="p-3 bg-teal-50 rounded-lg text-teal-600 mb-3 border border-teal-100">
                      <FileUp className="h-6 w-6" />
                    </div>
                    <span className="text-sm font-semibold text-slate-900 block mb-1">Drag & drop new PDF here</span>
                    <span className="text-xs text-slate-500">or click to browse local files</span>
                  </div>
                ) : (
                  <div className="flex items-center justify-between p-4 bg-white border border-slate-200 rounded-lg shadow-sm min-h-[100px]">
                    <div className="flex items-center gap-3 truncate">
                      <div className="p-2.5 bg-emerald-50 text-emerald-600 rounded-lg border border-emerald-200">
                        <FileCheck className="h-5 w-5" />
                      </div>
                      <div className="truncate">
                        <span className="text-sm font-semibold text-slate-900 block truncate">{newFile.name}</span>
                        <span className="text-xs text-slate-500 font-mono">{(newFile.size / 1024 / 1024).toFixed(2)} MB</span>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setNewFile(null)}
                      className="text-slate-400 hover:text-rose-600"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                )}
              </div>
            </div>

            <div className="pt-6 border-t border-slate-200 flex justify-end">
              <Button
                onClick={handleCompare}
                disabled={!oldFile || !newFile}
                size="lg"
              >
                Compare Contracts
                <ArrowRight className="h-4 w-4" />
              </Button>
            </div>
          </Card>

          {/* Right: History Panel */}
          <Card className="space-y-4">
            <div className="flex items-center gap-2 pb-2 border-b border-slate-200">
              <History className="h-4 w-4 text-teal-600" />
              <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-700">Comparison History</h2>
            </div>

            <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
              {pastComparisons.length === 0 ? (
                <div className="text-center py-12 text-slate-500 space-y-2">
                  <FileText className="h-8 w-8 mx-auto text-slate-300" />
                  <p className="text-xs font-semibold uppercase tracking-wide">No history found</p>
                  <p className="text-xs leading-relaxed max-w-xs mx-auto">Compare your first contract versions to save them in database history.</p>
                </div>
              ) : (
                pastComparisons.map((cmp) => (
                  <button
                    type="button"
                    key={cmp.id}
                    onClick={() => loadPastResult(cmp)}
                    className="w-full text-left p-3 bg-slate-50 border border-slate-200 hover:border-teal-300 hover:bg-teal-50/50 rounded-lg transition-all space-y-2"
                  >
                    <div className="flex justify-between items-start">
                      <span className="text-sm font-semibold text-slate-900 truncate pr-2">{cmp.supplier_name}</span>
                      <Badge variant={cmp.status === 'COMPLETE' ? 'success' : 'high'}>
                        {cmp.status}
                      </Badge>
                    </div>
                    {cmp.diff_result && (
                      <div className="flex justify-between items-center text-xs text-slate-500">
                        <span>Overall: <strong className="text-slate-700">{cmp.diff_result.overall_impact}</strong></span>
                        <span>{cmp.diff_result.changes?.length || 0} change(s)</span>
                      </div>
                    )}
                  </button>
                ))
              )}
            </div>
          </Card>
        </div>
      )}

      {/* Loading Screen */}
      {isLoading && (
        <Card className="p-12 text-center max-w-2xl mx-auto space-y-6">
          <div className="relative w-16 h-16 mx-auto">
            <div className="absolute inset-0 border-4 border-teal-100 rounded-full" />
            <div className="absolute inset-0 border-4 border-teal-600 border-t-transparent rounded-full animate-spin" />
            <Loader2 className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-6 w-6 text-teal-600 animate-pulse" />
          </div>

          <div className="space-y-2">
            <h3 className="text-base font-semibold text-slate-900 uppercase tracking-wide">Analyzing Contract Revisions</h3>
            <p className="text-sm text-teal-600 font-medium">{progress}</p>
            <p className="text-xs text-slate-500 max-w-sm mx-auto leading-relaxed">
              We extract service parameters and pricing rules using Vertex AI Gemini to build a structured rule difference.
            </p>
          </div>
        </Card>
      )}

      {/* Results Screen */}
      {result && !isLoading && (
        <div className="space-y-6">
          {/* Action Back Row */}
          <div className="flex justify-between items-center">
            <Button variant="secondary" size="sm" onClick={resetComparator}>
              ← Compare Another
            </Button>
            <div className="text-xs text-slate-500 font-mono">
              ID: {comparisonId}
            </div>
          </div>

          {/* executive summary banner */}
          <Card className="grid grid-cols-1 md:grid-cols-4 gap-6 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 rounded-full bg-teal-50 blur-3xl pointer-events-none" />

            <div className="md:col-span-3 space-y-4">
              <div className="flex flex-wrap items-center gap-3">
                <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Supplier:</span>
                <span className="text-sm font-semibold text-slate-900">{result.supplier_name}</span>
                <span className={`inline-flex items-center px-2.5 py-1 text-xs font-semibold uppercase border rounded-full ${getImpactBadgeColor(result.overall_impact)}`}>
                  Overall Impact: {result.overall_impact}
                </span>
              </div>

              <div className="space-y-1.5">
                <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Executive Summary</h3>
                <p className="text-sm text-slate-700 leading-relaxed">
                  {result.summary}
                </p>
              </div>

              {/* Stats row */}
              <div className="flex flex-wrap gap-4 pt-2 text-xs font-semibold text-slate-600">
                <div className="flex items-center gap-1">
                  <span className="h-2 w-2 rounded-full bg-rose-500" />
                  <span>{result.worse_count || 0} Worse</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="h-2 w-2 rounded-full bg-emerald-500" />
                  <span>{result.better_count || 0} Better</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="h-2 w-2 rounded-full bg-slate-400" />
                  <span>{result.neutral_count || 0} Neutral</span>
                </div>
                <div className="flex items-center gap-1 border-l border-slate-200 pl-4">
                  <span>Total Changes: {result.changes?.length || 0}</span>
                </div>
              </div>
            </div>

            {/* Short contract identifiers */}
            <div className="md:col-span-1 border-t md:border-t-0 md:border-l border-slate-200 pt-4 md:pt-0 md:pl-6 flex flex-col justify-center space-y-3">
              <div className="space-y-1">
                <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Old Agreement ID</span>
                <span className="text-sm font-semibold text-slate-700 block font-mono truncate">{result.old_contract_id || 'Unknown'}</span>
              </div>
              <div className="space-y-1">
                <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">New Agreement ID</span>
                <span className="text-sm font-semibold text-teal-600 block font-mono truncate">{result.new_contract_id || 'Unknown'}</span>
              </div>
            </div>
          </Card>

          {/* Negotiation points card */}
          {result.negotiation_flags && result.negotiation_flags.length > 0 && (
            <Card className="bg-rose-50/50 border-rose-200 space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-rose-200">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-rose-600" />
                  <h3 className="text-xs font-semibold uppercase tracking-wide text-rose-700">Core Pushback & Negotiation Points</h3>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleCopyNegotiationPoints}
                  className="text-rose-700 hover:text-rose-800 hover:bg-rose-100/50 flex items-center gap-1.5 px-2 py-1 text-xs"
                  title="Copy negotiation points to clipboard"
                >
                  {copied ? (
                    <>
                      <Check className="h-3.5 w-3.5" />
                      <span>Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="h-3.5 w-3.5" />
                      <span>Copy All</span>
                    </>
                  )}
                </Button>
              </div>
              <ul className="space-y-3 text-sm text-rose-800">
                {result.negotiation_flags.map((flag, idx) => (
                  <li key={idx} className="flex items-start gap-2.5">
                    <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-rose-500 shrink-0" />
                    <span className="leading-relaxed">{flag}</span>
                  </li>
                ))}
              </ul>
            </Card>
          )}

          {/* Side by side differences table */}
          <Card padding={false}>
            <div className="px-6 py-4 border-b border-slate-200 bg-slate-50">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-700">Detailed Rule Changes</h3>
            </div>

            <Table className="border-0 rounded-none">
              <TableHead>
                <tr>
                  <TableCell header>Rule / Applies To</TableCell>
                  <TableCell header>Impact</TableCell>
                  <TableCell header>Old Term</TableCell>
                  <TableCell header>New Term</TableCell>
                  <TableCell header>Description</TableCell>
                </tr>
              </TableHead>
              <TableBody>
                {result.changes && result.changes.length > 0 ? (
                  result.changes.map((change, idx) => {
                    const styles = getChangeTypeStyles(change.change_type, change.impact);
                    return (
                      <TableRow key={idx} className={styles.rowBg}>
                        <TableCell className="space-y-1">
                          <span className="font-semibold text-slate-900 block capitalize">{change.rule_type.replace('_', ' ')}</span>
                          <span className="text-xs text-slate-500">{change.applies_to}</span>
                        </TableCell>
                        <TableCell>
                          <span className={`inline-flex items-center px-2 py-1 text-xs font-semibold uppercase border rounded-full ${styles.badge}`}>
                            {styles.badgeText}
                          </span>
                        </TableCell>
                        <TableCell className="space-y-1">
                          <span className="text-slate-600 block">
                            {change.old_rule ? (
                              change.old_rule.flat_unit_price !== undefined && change.old_rule.flat_unit_price !== null ? (
                                `Flat Price: $${change.old_rule.flat_unit_price}`
                              ) : change.old_rule.tiers && change.old_rule.tiers.length > 0 ? (
                                `${change.old_rule.tiers.length} Tiers`
                              ) : change.old_rule.sla_threshold_pct !== undefined && change.old_rule.sla_threshold_pct !== null ? (
                                `SLA Uptime: ${change.old_rule.sla_threshold_pct * 100}%`
                              ) : change.old_rule.penalty_pct !== undefined && change.old_rule.penalty_pct !== null ? (
                                `Penalty Credit: ${change.old_rule.penalty_pct * 100}%`
                              ) : change.old_rule.discount_pct !== undefined && change.old_rule.discount_pct !== null ? (
                                `Discount: ${change.old_rule.discount_pct * 100}%`
                              ) : (
                                'Configured'
                              )
                            ) : (
                              <span className="text-slate-400 italic">None</span>
                            )}
                          </span>
                          {change.old_clause && (
                            <span className="text-xs font-mono text-slate-500" title="Reference Clause">
                              Clause: {change.old_clause}
                            </span>
                          )}
                        </TableCell>
                        <TableCell className="space-y-1">
                          <span className="text-slate-900 font-medium block">
                            {change.new_rule ? (
                              change.new_rule.flat_unit_price !== undefined && change.new_rule.flat_unit_price !== null ? (
                                `Flat Price: $${change.new_rule.flat_unit_price}`
                              ) : change.new_rule.tiers && change.new_rule.tiers.length > 0 ? (
                                `${change.new_rule.tiers.length} Tiers`
                              ) : change.new_rule.sla_threshold_pct !== undefined && change.new_rule.sla_threshold_pct !== null ? (
                                `SLA Uptime: ${change.new_rule.sla_threshold_pct * 100}%`
                              ) : change.new_rule.penalty_pct !== undefined && change.new_rule.penalty_pct !== null ? (
                                `Penalty Credit: ${change.new_rule.penalty_pct * 100}%`
                              ) : change.new_rule.discount_pct !== undefined && change.new_rule.discount_pct !== null ? (
                                `Discount: ${change.new_rule.discount_pct * 100}%`
                              ) : (
                                'Configured'
                              )
                            ) : (
                              <span className="text-slate-400 italic">None</span>
                            )}
                          </span>
                          {change.new_clause && (
                            <span className="text-xs font-mono text-teal-600" title="Reference Clause">
                              Clause: {change.new_clause}
                            </span>
                          )}
                        </TableCell>
                        <TableCell className="max-w-sm leading-relaxed">
                          {change.description}
                        </TableCell>
                      </TableRow>
                    );
                  })
                ) : (
                  <TableRow>
                    <TableCell colSpan={5} className="p-8 text-center text-slate-500">
                      No pricing differences or rule changes were found between these two contract versions.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </Card>
        </div>
      )}
    </div>
  );
}
