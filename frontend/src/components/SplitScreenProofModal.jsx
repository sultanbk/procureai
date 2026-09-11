import React, { useState, useEffect, useMemo } from 'react';
import { 
  X, 
  ExternalLink, 
  Copy, 
  Check, 
  FileText, 
  ShieldAlert, 
  AlertTriangle, 
  CheckCircle2, 
  Eye, 
  ChevronRight, 
  FileDown, 
  Maximize2,
  Sparkles,
  Layers
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

  // Sync initial finding if passed
  useEffect(() => {
    if (initialFindingId) {
      setSelectedFindingId(initialFindingId);
    } else if (discrepancies.length > 0 && !selectedFindingId) {
      setSelectedFindingId(discrepancies[0].finding_id);
    }
  }, [initialFindingId, discrepancies]);

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
  }, [isOpen, auditId, selectedFindingId, proofsMap]);

  const activeFinding = useMemo(() => {
    return discrepancies.find((d) => d.finding_id === selectedFindingId);
  }, [discrepancies, selectedFindingId]);

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

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-md p-2 sm:p-4">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full h-[95vh] max-w-[98vw] flex flex-col shadow-2xl overflow-hidden text-slate-100 animate-scale-up">
        
        {/* Top Header & Finding Navigator Bar */}
        <header className="px-5 py-3.5 border-b border-slate-800 bg-slate-900/90 flex flex-col md:flex-row md:items-center justify-between gap-3 shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-teal-500/20 text-teal-300 border border-teal-500/30">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white tracking-tight font-display">
                  Visual Click-to-Proof Inspector
                </h2>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 uppercase tracking-wider">
                  Side-by-Side Verification
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Instant synchronized verification between billed invoice lines and governing contract clauses.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 self-end md:self-auto">
            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
              title="Close Viewer (Esc)"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </header>

        {/* Discrepancy Chip Selector Carousel */}
        <div className="px-5 py-2.5 bg-slate-950/60 border-b border-slate-800/80 flex items-center gap-2 overflow-x-auto shrink-0 scrollbar-none">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mr-1 shrink-0 flex items-center gap-1">
            <Eye className="w-3.5 h-3.5 text-teal-400" /> Discrepancies ({discrepancies.length}):
          </span>

          {discrepancies.map((d) => {
            const isSelected = d.finding_id === selectedFindingId;
            const deltaNum = Math.abs(parseFloat(d.delta || 0));

            return (
              <button
                key={d.finding_id}
                onClick={() => setSelectedFindingId(d.finding_id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold shrink-0 transition-all flex items-center gap-2 border ${
                  isSelected
                    ? 'bg-teal-500/20 text-teal-200 border-teal-400 shadow-sm ring-1 ring-teal-400/50'
                    : 'bg-slate-800/60 text-slate-300 border-slate-700/60 hover:bg-slate-800 hover:border-slate-600'
                }`}
              >
                <span className="font-mono font-bold">{d.finding_id}</span>
                <span className="truncate max-w-[120px] text-[11px]">{d.description}</span>
                <span className="font-mono font-bold text-rose-400 text-[11px]">
                  -${deltaNum.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                </span>
              </button>
            );
          })}
        </div>

        {/* Finding Quick Summary Banner */}
        {activeFinding && (
          <div className="px-6 py-2.5 bg-slate-850 border-b border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-xs shrink-0">
            <div className="flex items-center gap-2.5">
              <span className={`px-2 py-0.5 rounded text-[10px] font-extrabold uppercase tracking-wider ${
                activeFinding.severity === 'CRITICAL'
                  ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                  : activeFinding.severity === 'HIGH'
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                  : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
              }`}>
                {activeFinding.severity}
              </span>
              <span className="font-bold text-white text-sm">{activeFinding.description}</span>
            </div>

            <div className="flex items-center gap-4">
              <div className="text-slate-400 text-[11px]">
                Expected: <strong className="text-emerald-400 font-mono">${parseFloat(activeFinding.unit_price_expected || 0).toFixed(2)}</strong>
                <span className="mx-1.5">•</span>
                Billed: <strong className="text-rose-400 font-mono">${parseFloat(activeFinding.unit_price_charged || 0).toFixed(2)}</strong>
              </div>
              <div className="font-mono font-bold text-rose-400 text-sm bg-rose-500/10 px-2.5 py-0.5 rounded border border-rose-500/20">
                Leakage: -${Math.abs(parseFloat(activeFinding.delta || 0)).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </div>
            </div>
          </div>
        )}

        {/* Split Screen Dual Viewport */}
        <div className="flex-1 grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-slate-800 min-h-0 bg-slate-950">
          
          {/* LEFT VIEWPORT: Billed Invoice */}
          <div className="flex flex-col h-full min-h-0">
            {/* Viewport Toolbar */}
            <div className="px-4 py-2.5 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between text-xs shrink-0">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
                <span className="font-bold text-rose-300 uppercase tracking-wider text-[10px]">
                  Billed Invoice
                </span>
                <span className="text-slate-400 font-mono text-[11px]">
                  {currentProof?.invoice?.filename || 'Invoice.pdf'}
                </span>
                <span className="px-2 py-0.5 rounded bg-slate-800 text-[10px] font-bold text-slate-300">
                  Page {currentProof?.invoice?.page_number || 1} of {currentProof?.invoice?.total_pages || 1}
                </span>
              </div>

              <div className="flex items-center gap-1.5">
                {currentProof?.invoice?.document_id && (
                  <a
                    href={`${API_BASE}/audit/${auditId}/documents/${currentProof.invoice.document_id}`}
                    target="_blank"
                    rel="noreferrer"
                    className="p-1.5 text-slate-400 hover:text-white rounded hover:bg-slate-800 transition-colors"
                    title="Open Full Invoice in New Tab"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                )}
              </div>
            </div>

            {/* Document Frame with Red Bounding Box Callout */}
            <div className="flex-1 relative overflow-hidden bg-slate-900/40">
              {/* Floating Bounding Box Banner */}
              <div className="absolute top-3 left-3 right-3 z-10 bg-rose-950/90 border border-rose-500/50 rounded-xl p-3 shadow-lg backdrop-blur-sm flex items-center justify-between gap-3 animate-fade-in">
                <div className="flex items-center gap-2.5">
                  <div className="w-2 h-2 rounded-full bg-rose-500 animate-ping shrink-0" />
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-rose-300 block">
                      Target Billed Line Item ({activeFinding?.line_id || 'Line Item'})
                    </span>
                    <p className="text-xs font-semibold text-white mt-0.5 font-mono">
                      Billed: ${parseFloat(activeFinding?.unit_price_charged || 0).toFixed(2)}/unit • Qty: {activeFinding?.quantity || 1}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => handleCopy(activeFinding?.description || '', 'Invoice Item')}
                  className="px-2 py-1 rounded bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 text-[10px] font-bold transition-colors flex items-center gap-1 shrink-0"
                >
                  {copiedText === 'Invoice Item' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  Copy
                </button>
              </div>

              {/* PDF Embed / iframe */}
              {currentProof?.invoice?.document_id ? (
                <iframe
                  title="Invoice Proof"
                  src={`${API_BASE}/audit/${auditId}/documents/${currentProof.invoice.document_id}#page=${currentProof.invoice.page_number || 1}`}
                  className="w-full h-full border-0 bg-white"
                />
              ) : (
                <div className="h-full flex items-center justify-center text-xs text-slate-500">
                  Loading invoice view...
                </div>
              )}
            </div>

            {/* Invoice Line Excerpt Footer */}
            <div className="p-3 bg-slate-900 border-t border-slate-800 text-xs shrink-0 flex items-center justify-between gap-3">
              <div className="truncate">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Raw Description:</span>
                <span className="text-slate-300 font-mono text-[11px] truncate block">{activeFinding?.description}</span>
              </div>
              <span className="font-mono font-bold text-rose-400 text-xs shrink-0">
                Billed: ${parseFloat(activeFinding?.line_total_charged || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </span>
            </div>
          </div>

          {/* RIGHT VIEWPORT: Governing Contract */}
          <div className="flex flex-col h-full min-h-0">
            {/* Viewport Toolbar */}
            <div className="px-4 py-2.5 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between text-xs shrink-0">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
                <span className="font-bold text-amber-300 uppercase tracking-wider text-[10px]">
                  Governing Contract
                </span>
                <span className="text-slate-400 font-mono text-[11px]">
                  {currentProof?.contract?.filename || 'Contract.pdf'}
                </span>
                <span className="px-2 py-0.5 rounded bg-slate-800 text-[10px] font-bold text-slate-300">
                  Page {currentProof?.contract?.page_number || 1} of {currentProof?.contract?.total_pages || 1}
                </span>
              </div>

              <div className="flex items-center gap-1.5">
                <button
                  onClick={handleDownloadBreachPages}
                  className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-[10px] font-bold transition-colors flex items-center gap-1"
                  title="Download contract breach pages"
                >
                  <FileDown className="w-3 h-3" /> Breach Pages
                </button>
                <a
                  href={`${API_BASE}/audit/${auditId}/documents/contract`}
                  target="_blank"
                  rel="noreferrer"
                  className="p-1.5 text-slate-400 hover:text-white rounded hover:bg-slate-800 transition-colors"
                  title="Open Full Contract in New Tab"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            </div>

            {/* Document Frame with Amber Bounding Box Callout */}
            <div className="flex-1 relative overflow-hidden bg-slate-900/40">
              {/* Floating Bounding Box Banner */}
              <div className="absolute top-3 left-3 right-3 z-10 bg-amber-950/90 border border-amber-500/50 rounded-xl p-3 shadow-lg backdrop-blur-sm flex items-center justify-between gap-3 animate-fade-in">
                <div className="flex items-center gap-2.5">
                  <div className="w-2 h-2 rounded-full bg-amber-400 animate-ping shrink-0" />
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-amber-300 block">
                      Violated Contract Term ({activeFinding?.clause_reference || 'Clause'})
                    </span>
                    <p className="text-xs font-semibold text-white mt-0.5 font-mono">
                      Authorized Rate: ${parseFloat(activeFinding?.unit_price_expected || 0).toFixed(2)}/unit
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => handleCopy(activeFinding?.clause_text || activeFinding?.description || '', 'Contract Clause')}
                  className="px-2 py-1 rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 text-[10px] font-bold transition-colors flex items-center gap-1 shrink-0"
                >
                  {copiedText === 'Contract Clause' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  Copy
                </button>
              </div>

              {/* PDF Embed / iframe */}
              <iframe
                title="Contract Proof"
                src={`${API_BASE}/audit/${auditId}/documents/contract#page=${currentProof?.contract?.page_number || 1}`}
                className="w-full h-full border-0 bg-white"
              />
            </div>

            {/* Contract Clause Excerpt Footer */}
            <div className="p-3 bg-slate-900 border-t border-slate-800 text-xs shrink-0 flex items-center justify-between gap-3">
              <div className="truncate">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Quoted Clause:</span>
                <span className="text-slate-300 italic text-[11px] truncate block">
                  "{activeFinding?.clause_text || 'Exact contract rule extracted by Critic'}"
                </span>
              </div>
              <span className="font-mono font-bold text-emerald-400 text-xs shrink-0">
                Expected: ${parseFloat(activeFinding?.line_total_expected || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </span>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
