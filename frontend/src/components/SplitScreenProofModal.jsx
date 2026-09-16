import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { 
  X, 
  ExternalLink, 
  Copy, 
  Check, 
  FileText, 
  FileCheck,
  ShieldAlert, 
  AlertTriangle, 
  CheckCircle2, 
  Eye, 
  ChevronRight, 
  ChevronLeft,
  FileDown, 
  Maximize2,
  Minimize2,
  Columns,
  Sparkles,
  Layers,
  ArrowRight,
  Info,
  SlidersHorizontal
} from 'lucide-react';
import { getFindingProof, getAllFindingProofs, downloadBreachPages } from '../api';
import { useToast } from './ui/ToastProvider';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export default function SplitScreenProofModal({ 
  isOpen, 
  onClose, 
  auditId, 
  initialFindingId, 
  discrepancies = [] 
}) {
  const { toast } = useToast();
  const [selectedFindingId, setSelectedFindingId] = useState(initialFindingId || discrepancies[0]?.finding_id || '');
  const [proofsMap, setProofsMap] = useState({});
  const [currentProof, setCurrentProof] = useState(null);
  const [loading, setLoading] = useState(true);
  const [copiedText, setCopiedText] = useState(null);
  const [viewMode, setViewMode] = useState('split'); // 'split' | 'invoice' | 'contract'
  const [showCallout, setShowCallout] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Sync initial finding if passed
  useEffect(() => {
    if (initialFindingId) {
      setSelectedFindingId(initialFindingId);
    } else if (discrepancies.length > 0 && !selectedFindingId) {
      setSelectedFindingId(discrepancies[0].finding_id);
    }
  }, [initialFindingId, discrepancies, selectedFindingId]);

  // Load all proofs for audit
  useEffect(() => {
    if (isOpen && auditId) {
      setLoading(true);
      getAllFindingProofs(auditId)
        .then((res) => {
          setProofsMap(res.proofs || {});
        })
        .catch((err) => {
          console.error("Failed to batch load finding proofs:", err);
        })
        .finally(() => {
          setLoading(false);
        });
    }
  }, [isOpen, auditId]);

  // Fetch or resolve current proof when selectedFindingId changes
  useEffect(() => {
    if (!isOpen || !auditId || !selectedFindingId) return;

    if (proofsMap[selectedFindingId]) {
      setCurrentProof(proofsMap[selectedFindingId]);
    } else {
      getFindingProof(auditId, selectedFindingId)
        .then((p) => {
          setCurrentProof(p);
          setProofsMap((prev) => ({ ...prev, [selectedFindingId]: p }));
        })
        .catch((err) => {
          toast(err.message || 'Failed to load proof coordinates', 'error');
        });
    }
  }, [isOpen, auditId, selectedFindingId, proofsMap, toast]);

  const activeIndex = useMemo(() => {
    return discrepancies.findIndex((d) => d.finding_id === selectedFindingId);
  }, [discrepancies, selectedFindingId]);

  const activeFinding = useMemo(() => {
    return discrepancies[activeIndex] || discrepancies[0] || null;
  }, [discrepancies, activeIndex]);

  const handlePrevFinding = useCallback(() => {
    if (discrepancies.length <= 1) return;
    const prevIdx = (activeIndex - 1 + discrepancies.length) % discrepancies.length;
    setSelectedFindingId(discrepancies[prevIdx].finding_id);
  }, [activeIndex, discrepancies]);

  const handleNextFinding = useCallback(() => {
    if (discrepancies.length <= 1) return;
    const nextIdx = (activeIndex + 1) % discrepancies.length;
    setSelectedFindingId(discrepancies[nextIdx].finding_id);
  }, [activeIndex, discrepancies]);

  // Keyboard navigation shortcuts
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'ArrowLeft') {
        handlePrevFinding();
      } else if (e.key === 'ArrowRight') {
        handleNextFinding();
      } else if (e.key === '1') {
        setViewMode('split');
      } else if (e.key === '2') {
        setViewMode('invoice');
      } else if (e.key === '3') {
        setViewMode('contract');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose, handlePrevFinding, handleNextFinding]);

  const handleCopy = (text, label) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedText(label);
    toast(`${label} copied to clipboard`, 'success');
    setTimeout(() => setCopiedText(null), 2000);
  };

  const handleDownloadBreachPages = async () => {
    if (!auditId || !selectedFindingId) return;
    try {
      const blob = await downloadBreachPages(auditId, selectedFindingId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${auditId}_${selectedFindingId}_breach_pages.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      toast('Breach pages downloaded', 'success');
    } catch (err) {
      toast(err.message || 'Failed to download breach pages', 'error');
    }
  };

  if (!isOpen) return null;

  const chargedRate = parseFloat(activeFinding?.unit_price_charged || 0);
  const expectedRate = parseFloat(activeFinding?.unit_price_expected || 0);
  const qty = activeFinding?.quantity || 1;
  const deltaNum = Math.abs(parseFloat(activeFinding?.delta || 0));

  const severityBadge = (severity) => {
    switch (severity?.toUpperCase()) {
      case 'CRITICAL':
        return 'bg-rose-50 text-rose-700 border-rose-200 ring-1 ring-rose-300/50';
      case 'HIGH':
        return 'bg-amber-50 text-amber-800 border-amber-200 ring-1 ring-amber-300/50';
      case 'MEDIUM':
        return 'bg-sky-50 text-sky-800 border-sky-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-2 sm:p-4">
      <div 
        className={`bg-slate-50 border border-slate-200/90 rounded-2xl w-full flex flex-col shadow-2xl overflow-hidden text-slate-800 transition-all duration-300 ${
          isFullscreen ? 'h-full max-w-none rounded-none' : 'h-[95vh] max-w-[98vw]'
        }`}
      >
        
        {/* TOP HEADER: Clean, Professional Enterprise Banner */}
        <header className="px-5 py-3 bg-white border-b border-slate-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shrink-0 shadow-xs">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-teal-50 text-teal-700 border border-teal-200/80 shadow-xs">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-slate-900 tracking-tight font-display">
                  Split-Screen Audit Proof Inspector
                </h2>
                <span className="hidden sm:inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-teal-50 text-teal-800 border border-teal-200">
                  <Sparkles className="w-3 h-3 text-teal-600" />
                  Synchronized Verification
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Side-by-side evidence matching the billed line item against governing contractual clauses.
              </p>
            </div>
          </div>

          {/* Top Controls: View Mode, Toggle Context, Fullscreen & Close */}
          <div className="flex items-center gap-2 self-end sm:self-auto">
            {/* View Mode Segmented Controls */}
            <div className="flex items-center p-0.5 bg-slate-100 rounded-lg border border-slate-200 text-xs font-semibold text-slate-600">
              <button
                type="button"
                onClick={() => setViewMode('split')}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md transition-all ${
                  viewMode === 'split' 
                    ? 'bg-white text-slate-900 shadow-xs font-bold' 
                    : 'hover:text-slate-900 hover:bg-slate-200/60'
                }`}
                title="Split Screen 50/50 View (Press 1)"
              >
                <Columns className="w-3.5 h-3.5 text-teal-600" />
                <span className="hidden md:inline">Split</span>
              </button>
              <button
                type="button"
                onClick={() => setViewMode('invoice')}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md transition-all ${
                  viewMode === 'invoice' 
                    ? 'bg-white text-rose-700 shadow-xs font-bold' 
                    : 'hover:text-slate-900 hover:bg-slate-200/60'
                }`}
                title="Focus on Billed Invoice (Press 2)"
              >
                <FileText className="w-3.5 h-3.5 text-rose-600" />
                <span className="hidden md:inline">Invoice</span>
              </button>
              <button
                type="button"
                onClick={() => setViewMode('contract')}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md transition-all ${
                  viewMode === 'contract' 
                    ? 'bg-white text-emerald-700 shadow-xs font-bold' 
                    : 'hover:text-slate-900 hover:bg-slate-200/60'
                }`}
                title="Focus on Governing Contract (Press 3)"
              >
                <FileCheck className="w-3.5 h-3.5 text-emerald-600" />
                <span className="hidden md:inline">Contract</span>
              </button>
            </div>

            {/* Toggle Highlight Details */}
            <button
              type="button"
              onClick={() => setShowCallout(!showCallout)}
              className={`p-1.5 rounded-lg border transition-colors text-xs font-medium flex items-center gap-1 ${
                showCallout
                  ? 'bg-slate-100 text-slate-700 border-slate-200 hover:bg-slate-200'
                  : 'bg-white text-slate-500 border-slate-200 hover:text-slate-900 hover:bg-slate-50'
              }`}
              title={showCallout ? 'Hide Top Highlights (maximize document viewport)' : 'Show Top Highlights'}
            >
              <SlidersHorizontal className="w-3.5 h-3.5" />
              <span className="hidden lg:inline">{showCallout ? 'Hide Highlights' : 'Show Highlights'}</span>
            </button>

            {/* Fullscreen Toggle */}
            <button
              type="button"
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="p-1.5 text-slate-500 hover:text-slate-900 rounded-lg hover:bg-slate-100 border border-slate-200 transition-colors"
              title={isFullscreen ? 'Exit Fullscreen' : 'Maximize Fullscreen'}
            >
              {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>

            {/* Close Button */}
            <button
              type="button"
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100 transition-colors ml-1"
              title="Close Proof Inspector (Esc)"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </header>

        {/* FINDING NAVIGATOR CAROUSEL: Clean, high-contrast, easy to switch */}
        <div className="px-5 py-2.5 bg-slate-100/80 border-b border-slate-200 flex items-center gap-2 shrink-0">
          <div className="flex items-center gap-1 text-xs font-semibold text-slate-600 shrink-0 mr-1">
            <button
              type="button"
              onClick={handlePrevFinding}
              disabled={discrepancies.length <= 1}
              className="p-1 rounded-md bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-xs"
              title="Previous Discrepancy (← Left Arrow)"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>
            <span className="px-1.5 py-0.5 text-[11px] font-bold text-slate-500 font-mono">
              {activeIndex + 1}/{discrepancies.length}
            </span>
            <button
              type="button"
              onClick={handleNextFinding}
              disabled={discrepancies.length <= 1}
              className="p-1 rounded-md bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-xs"
              title="Next Discrepancy (→ Right Arrow)"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Scrollable Findings */}
          <div className="flex items-center gap-2 overflow-x-auto scrollbar-none py-0.5">
            {discrepancies.map((d, index) => {
              const isSelected = d.finding_id === selectedFindingId;
              const deltaVal = Math.abs(parseFloat(d.delta || 0));

              return (
                <button
                  key={d.finding_id}
                  type="button"
                  onClick={() => setSelectedFindingId(d.finding_id)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium shrink-0 transition-all flex items-center gap-2 border ${
                    isSelected
                      ? 'bg-white text-slate-900 border-teal-500 shadow-sm ring-2 ring-teal-500/20 font-semibold'
                      : 'bg-white/70 text-slate-600 border-slate-200 hover:bg-white hover:border-slate-300'
                  }`}
                >
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase border ${severityBadge(d.severity)}`}>
                    #{index + 1}
                  </span>
                  <span className="truncate max-w-[140px] text-xs">
                    {d.description}
                  </span>
                  <span className="font-mono font-bold text-rose-600 text-[11px] bg-rose-50 px-1.5 py-0.5 rounded border border-rose-100">
                    -${deltaVal.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* AT-A-GLANCE PROOF VERDICT BANNER */}
        {activeFinding && (
          <div className="mx-4 sm:mx-5 my-2.5 p-3.5 bg-white border border-slate-200/90 rounded-xl shadow-xs shrink-0 flex flex-col md:flex-row md:items-center justify-between gap-3">
            
            {/* Left: Plain-English breach description */}
            <div className="flex items-start gap-3 min-w-0">
              <span className={`px-2.5 py-1 rounded-md text-[11px] font-extrabold uppercase tracking-wider border shrink-0 mt-0.5 ${severityBadge(activeFinding.severity)}`}>
                {activeFinding.severity}
              </span>
              <div className="min-w-0">
                <h3 className="font-bold text-slate-900 text-sm tracking-tight truncate">
                  {activeFinding.description}
                </h3>
                <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-2">
                  <span>Governed by contract term:</span>
                  <span className="font-mono font-semibold text-slate-700 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                    {activeFinding.clause_reference || 'Contract Clause'}
                  </span>
                </p>
              </div>
            </div>

            {/* Right: Core Proof Comparison Metric (Charged vs Agreed = Overcharge) */}
            <div className="flex items-center gap-2 sm:gap-3 flex-wrap md:flex-nowrap shrink-0">
              {/* Billed */}
              <div className="px-3 py-1.5 rounded-lg bg-rose-50/80 border border-rose-200/90 text-left">
                <span className="text-[10px] font-bold text-rose-700 uppercase tracking-wide block">
                  Billed Rate
                </span>
                <span className="text-xs font-mono font-bold text-rose-900">
                  ${chargedRate.toFixed(2)}/unit
                </span>
              </div>

              <div className="text-slate-300 font-bold hidden sm:block">vs</div>

              {/* Authorized */}
              <div className="px-3 py-1.5 rounded-lg bg-emerald-50/80 border border-emerald-200/90 text-left">
                <span className="text-[10px] font-bold text-emerald-700 uppercase tracking-wide block">
                  Contract Rate
                </span>
                <span className="text-xs font-mono font-bold text-emerald-900">
                  ${expectedRate.toFixed(2)}/unit
                </span>
              </div>

              <ArrowRight className="w-3.5 h-3.5 text-slate-400 hidden md:block" />

              {/* Overcharge badge */}
              <div className="px-3.5 py-1.5 rounded-lg bg-rose-600 text-white shadow-xs text-left">
                <span className="text-[10px] font-bold uppercase tracking-wider block opacity-90">
                  Verified Overcharge
                </span>
                <span className="text-sm font-mono font-extrabold tracking-tight">
                  -${deltaNum.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* DUAL VIEWPORT BODY */}
        <div className="flex-1 px-4 sm:px-5 pb-4 min-h-0">
          <div className="h-full grid grid-cols-1 md:grid-cols-2 gap-4 min-h-0">
            
            {/* LEFT VIEWPORT: Billed Invoice */}
            {(viewMode === 'split' || viewMode === 'invoice') && (
              <div 
                className={`flex flex-col h-full min-h-0 bg-white border border-slate-200/90 rounded-xl overflow-hidden shadow-xs transition-all ${
                  viewMode === 'invoice' ? 'col-span-1 md:col-span-2' : ''
                }`}
              >
                {/* Viewport Header */}
                <div className="px-4 py-2.5 bg-rose-50/40 border-b border-rose-100 flex items-center justify-between gap-2 shrink-0">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-rose-100 text-rose-800 border border-rose-200">
                      <FileText className="w-3 h-3 text-rose-600" />
                      Billed Invoice
                    </span>
                    <span className="font-mono text-xs font-medium text-slate-700 truncate" title={currentProof?.invoice?.filename}>
                      {currentProof?.invoice?.filename || 'Invoice.pdf'}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-white text-[11px] font-semibold text-slate-600 border border-slate-200 shrink-0">
                      Page {currentProof?.invoice?.page_number || 1} of {currentProof?.invoice?.total_pages || 1}
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5 shrink-0">
                    <button
                      type="button"
                      onClick={() => handleCopy(activeFinding?.description || '', 'Invoice Item')}
                      className="px-2 py-1 rounded bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 text-xs font-medium transition-colors flex items-center gap-1"
                      title="Copy Invoice Item Citation"
                    >
                      {copiedText === 'Invoice Item' ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                      <span className="hidden sm:inline">Copy Citation</span>
                    </button>

                    {currentProof?.invoice?.document_id && (
                      <a
                        href={`${API_BASE}/audit/${auditId}/documents/${currentProof.invoice.document_id}`}
                        target="_blank"
                        rel="noreferrer"
                        className="p-1 text-slate-500 hover:text-slate-900 rounded hover:bg-white border border-transparent hover:border-slate-200 transition-colors"
                        title="Open Full Invoice in New Tab"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </a>
                    )}
                  </div>
                </div>

                {/* Docked Context Banner (Cleanly positioned above the iframe) */}
                {showCallout && (
                  <div className="px-4 py-2 bg-rose-50/70 border-b border-rose-100 flex items-center justify-between gap-3 text-xs shrink-0">
                    <div className="min-w-0">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-rose-700 block">
                        Target Line Item ({activeFinding?.line_id || 'Line Item'})
                      </span>
                      <p className="text-slate-800 font-medium truncate mt-0.5">
                        {activeFinding?.description}
                      </p>
                    </div>
                    <div className="text-right shrink-0">
                      <span className="text-[10px] text-rose-700 font-semibold block">Total Charged</span>
                      <span className="font-mono font-bold text-rose-800 text-xs">
                        ${parseFloat(activeFinding?.line_total_charged || (chargedRate * qty)).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                      </span>
                    </div>
                  </div>
                )}

                {/* Document Viewport / iframe */}
                <div className="flex-1 relative overflow-hidden bg-slate-100">
                  {currentProof?.invoice?.document_id ? (
                    <iframe
                      title="Invoice Proof"
                      src={`${API_BASE}/audit/${auditId}/documents/${currentProof.invoice.document_id}#page=${currentProof.invoice.page_number || 1}`}
                      className="w-full h-full border-0 bg-white"
                    />
                  ) : (
                    <div className="h-full flex flex-col items-center justify-center text-xs text-slate-500 gap-2">
                      <div className="w-6 h-6 border-2 border-rose-500 border-t-transparent rounded-full animate-spin" />
                      <span>Loading synchronized invoice view...</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* RIGHT VIEWPORT: Governing Contract */}
            {(viewMode === 'split' || viewMode === 'contract') && (
              <div 
                className={`flex flex-col h-full min-h-0 bg-white border border-slate-200/90 rounded-xl overflow-hidden shadow-xs transition-all ${
                  viewMode === 'contract' ? 'col-span-1 md:col-span-2' : ''
                }`}
              >
                {/* Viewport Header */}
                <div className="px-4 py-2.5 bg-emerald-50/40 border-b border-emerald-100 flex items-center justify-between gap-2 shrink-0">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-emerald-100 text-emerald-800 border border-emerald-200">
                      <FileCheck className="w-3 h-3 text-emerald-600" />
                      Governing Contract
                    </span>
                    <span className="font-mono text-xs font-medium text-slate-700 truncate" title={currentProof?.contract?.filename}>
                      {currentProof?.contract?.filename || 'Contract.pdf'}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-white text-[11px] font-semibold text-slate-600 border border-slate-200 shrink-0">
                      Page {currentProof?.contract?.page_number || 1} of {currentProof?.contract?.total_pages || 1}
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5 shrink-0">
                    <button
                      type="button"
                      onClick={handleDownloadBreachPages}
                      className="px-2 py-1 rounded bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 text-xs font-medium transition-colors flex items-center gap-1"
                      title="Download Contract Breach Pages"
                    >
                      <FileDown className="w-3.5 h-3.5 text-emerald-600" />
                      <span className="hidden sm:inline">Breach Pages</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => handleCopy(activeFinding?.clause_text || activeFinding?.description || '', 'Contract Clause')}
                      className="px-2 py-1 rounded bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 text-xs font-medium transition-colors flex items-center gap-1"
                      title="Copy Violated Clause Citation"
                    >
                      {copiedText === 'Contract Clause' ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                      <span className="hidden sm:inline">Copy Clause</span>
                    </button>

                    <a
                      href={`${API_BASE}/audit/${auditId}/documents/contract`}
                      target="_blank"
                      rel="noreferrer"
                      className="p-1 text-slate-500 hover:text-slate-900 rounded hover:bg-white border border-transparent hover:border-slate-200 transition-colors"
                      title="Open Full Contract in New Tab"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  </div>
                </div>

                {/* Docked Context Banner (Cleanly positioned above the iframe) */}
                {showCallout && (
                  <div className="px-4 py-2 bg-emerald-50/70 border-b border-emerald-100 flex items-center justify-between gap-3 text-xs shrink-0">
                    <div className="min-w-0">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-700 block">
                        Violated Rule ({activeFinding?.clause_reference || 'Clause'})
                      </span>
                      <p className="text-slate-800 italic font-mono text-[11px] truncate mt-0.5">
                        &ldquo;{activeFinding?.clause_text || 'Exact rule extracted by Critic'}&rdquo;
                      </p>
                    </div>
                    <div className="text-right shrink-0">
                      <span className="text-[10px] text-emerald-700 font-semibold block">Authorized Rate</span>
                      <span className="font-mono font-bold text-emerald-800 text-xs">
                        ${expectedRate.toFixed(2)}/unit
                      </span>
                    </div>
                  </div>
                )}

                {/* Document Viewport / iframe */}
                <div className="flex-1 relative overflow-hidden bg-slate-100">
                  <iframe
                    title="Contract Proof"
                    src={`${API_BASE}/audit/${auditId}/documents/contract#page=${currentProof?.contract?.page_number || 1}`}
                    className="w-full h-full border-0 bg-white"
                  />
                </div>
              </div>
            )}

          </div>
        </div>
      </div>
    </div>
  );
}
