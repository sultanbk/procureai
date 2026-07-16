/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Splits page layout to view contracts and invoices alongside reports.
 * 
 * What it means:
 * Document reviewer side-panel.
 * 
 * Importance in Project:
 * Medium. Integrates document inspection directly into report pages.
 */

import { useEffect, useMemo, useState } from 'react';
import {
  downloadBreachPages,
  fetchAuditDocumentBlob,
  getAuditDocuments,
} from '../api';
import {
  ChevronDown, ChevronUp, FileText, AlertTriangle, FolderOpen,
  Eye, ExternalLink, Copy, Check, FileDown
} from 'lucide-react';
import Button from './ui/Button';
import Card from './ui/Card';
import Badge from './ui/Badge';
import Spinner from './ui/Spinner';
import { useToast } from './ui/ToastProvider';

export default function AuditDocumentPanel({ auditId, discrepancies = [] }) {
  const { toast } = useToast();

  const [documents, setDocuments] = useState([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState('');
  const [selectedFindingId, setSelectedFindingId] =
    useState(discrepancies[0]?.finding_id || '');
  const [documentUrl, setDocumentUrl] = useState('');
  const [isLoadingDocument, setIsLoadingDocument] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  
  // Visual UI states
  const [activeTab, setActiveTab] = useState('documents'); // 'documents' | 'findings'
  const [copiedId, setCopiedId] = useState(null);

  const selectedFinding = useMemo(
    () => discrepancies.find((item) => item.finding_id === selectedFindingId),
    [discrepancies, selectedFindingId]
  );

  // Sync selected finding if it changes or gets initialized
  useEffect(() => {
    if (!selectedFindingId && discrepancies.length > 0) {
      setSelectedFindingId(discrepancies[0].finding_id);
    }
  }, [discrepancies, selectedFindingId]);

  useEffect(() => {
    let ignore = false;

    getAuditDocuments(auditId)
      .then((data) => {
        if (ignore) return;

        setDocuments(data.documents || []);
        setSelectedDocumentId((data.documents || [])[0]?.id || '');
      })
      .catch((err) =>
        toast(err.message || 'Failed to load uploaded files', 'error')
      );

    return () => {
      ignore = true;
    };
  }, [auditId, toast]);

  useEffect(() => {
    let ignore = false;
    let nextUrl = '';

    if (!auditId || !selectedDocumentId) return undefined;

    setIsLoadingDocument(true);

    fetchAuditDocumentBlob(auditId, selectedDocumentId)
      .then((blob) => {
        if (ignore) return;

        nextUrl = URL.createObjectURL(blob);

        setDocumentUrl((previousUrl) => {
          if (previousUrl) URL.revokeObjectURL(previousUrl);
          return nextUrl;
        });
      })
      .catch((err) =>
        toast(err.message || 'Failed to open uploaded file', 'error')
      )
      .finally(() => {
        if (!ignore) setIsLoadingDocument(false);
      });

    return () => {
      ignore = true;
      if (nextUrl) URL.revokeObjectURL(nextUrl);
    };
  }, [auditId, selectedDocumentId, toast]);

  useEffect(
    () => () => {
      if (documentUrl) URL.revokeObjectURL(documentUrl);
    },
    [documentUrl]
  );

  const handleDownloadBreachPages = async () => {
    if (!selectedFindingId) return;

    try {
      const blob = await downloadBreachPages(auditId, selectedFindingId);

      const url = URL.createObjectURL(blob);

      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `${auditId}_${selectedFindingId}_contract_pages.pdf`;

      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();

      URL.revokeObjectURL(url);
      toast('Breach pages downloaded successfully', 'success');
    } catch (err) {
      toast(err.message || 'Failed to download breach pages', 'error');
    }
  };

  const handleCopyText = (text, id) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    toast('Text copied to clipboard', 'success');
    setTimeout(() => setCopiedId(null), 2000);
  };

  // Find document details for header display
  const activeDocument = useMemo(
    () => documents.find((doc) => doc.id === selectedDocumentId),
    [documents, selectedDocumentId]
  );

  // Switch tabs and set selected finding/document
  const handleSelectFinding = (finding) => {
    setSelectedFindingId(finding.finding_id);
    
    // Check if the finding has an associated invoice or if it is a general contract rule discrepancy
    if (finding.clause_text && finding.clause_text !== 'CONFIRMED' && finding.clause_text !== 'N/A') {
      setSelectedDocumentId('contract');
    } else {
      // Find invoice matching the finding's invoice_id
      const invId = finding.invoice_id?.toLowerCase() || '';
      const invoiceDoc = documents.find(doc => 
        doc.type === 'invoice' && 
        (doc.filename.toLowerCase().includes(invId) || 
         invId.includes(doc.filename.toLowerCase().replace('.pdf', '')) ||
         doc.id.toLowerCase().includes(invId))
      );
      if (invoiceDoc) {
        setSelectedDocumentId(invoiceDoc.id);
      } else {
        // Fallback to contract
        setSelectedDocumentId('contract');
      }
    }
  };

  const handleOpenFullscreen = () => {
    if (documentUrl) {
      window.open(documentUrl, '_blank');
    }
  };

  if (documents.length === 0) return null;

  return (
    <Card className="print:hidden border border-slate-200 overflow-hidden shadow-sm transition-all duration-300">
      
      {/* Accordion Header */}
      <div
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between cursor-pointer bg-slate-50 hover:bg-slate-100/80 p-4 transition-colors border-b border-slate-200"
      >
        <div className="flex items-center gap-3">
          <div className="p-2 bg-teal-50 text-teal-600 border border-teal-100 rounded-lg">
            <FolderOpen className="h-4.5 w-4.5 stroke-[1.5]" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider font-display">
              Audited Files & Document Viewer
            </h3>
            <p className="text-slate-500 text-xs mt-0.5">
              Review original contracts, invoices, and pinpoint highlighted discrepancy clauses.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <Badge variant="secondary" className="bg-white border border-slate-200 text-slate-600 font-medium text-[10px]">
            {documents.length} Files
          </Badge>
          {isOpen ? (
            <ChevronUp className="h-4 w-4 text-slate-400 stroke-[1.5]" />
          ) : (
            <ChevronDown className="h-4 w-4 text-slate-400 stroke-[1.5]" />
          )}
        </div>
      </div>

      {/* Collapsible Content */}
      {isOpen && (
        <div className="p-4 bg-slate-50/50 space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            
            {/* Sidebar / Left Column */}
            <div className="lg:col-span-4 flex flex-col space-y-4 h-[620px]">
              
              {/* Tab Selector */}
              <div className="flex p-1 bg-slate-200/60 rounded-lg">
                <button
                  type="button"
                  onClick={() => setActiveTab('documents')}
                  className={`flex-1 flex items-center justify-center gap-2 py-1.5 text-xs font-semibold rounded-md transition-all ${
                    activeTab === 'documents'
                      ? 'bg-white text-slate-900 shadow-sm'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <FolderOpen className="h-3.5 w-3.5 stroke-[1.5]" />
                  Documents ({documents.length})
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('findings')}
                  className={`flex-1 flex items-center justify-center gap-2 py-1.5 text-xs font-semibold rounded-md transition-all ${
                    activeTab === 'findings'
                      ? 'bg-white text-slate-900 shadow-sm'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <AlertTriangle className="h-3.5 w-3.5 stroke-[1.5]" />
                  Breaches ({discrepancies.length})
                </button>
              </div>

              {/* Tab Content List Container */}
              <div className="flex-1 overflow-y-auto pr-1 space-y-2">
                {activeTab === 'documents' ? (
                  documents.map((doc) => {
                    const isSelected = selectedDocumentId === doc.id;
                    return (
                      <div
                        key={doc.id}
                        onClick={() => setSelectedDocumentId(doc.id)}
                        className={`group p-3 rounded-lg border text-left cursor-pointer transition-all duration-200 hover:-translate-y-0.5 ${
                          isSelected
                            ? 'border-teal-500 bg-teal-50/50 ring-1 ring-teal-500 shadow-sm'
                            : 'border-slate-200 bg-white hover:border-slate-300 hover:shadow-sm'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <div className={`p-1.5 rounded ${
                            isSelected 
                              ? 'bg-teal-100 text-teal-700' 
                              : 'bg-slate-100 text-slate-500 group-hover:bg-slate-200 group-hover:text-slate-700'
                          } transition-colors`}>
                            <FileText className="h-4 w-4 stroke-[1.5]" />
                          </div>
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center justify-between gap-1.5">
                              <span className="font-semibold text-slate-800 text-xs block truncate font-display">
                                {doc.label}
                              </span>
                              {isSelected && (
                                <span className="h-1.5 w-1.5 rounded-full bg-teal-500 shrink-0" />
                              )}
                            </div>
                            <span className="text-slate-500 text-[10px] block truncate mt-0.5 font-mono">
                              {doc.filename}
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })
                ) : discrepancies.length === 0 ? (
                  <div className="text-center py-8 text-slate-400 text-xs font-medium">
                    No discrepancy findings in this report.
                  </div>
                ) : (
                  discrepancies.map((finding) => {
                    const isSelected = selectedFindingId === finding.finding_id;
                    let severityClass = 'badge-medium';
                    if (finding.severity === 'CRITICAL') severityClass = 'badge-critical';
                    if (finding.severity === 'HIGH') severityClass = 'badge-high';
                    if (finding.severity === 'LOW') severityClass = 'badge-low';

                    return (
                      <div
                        key={finding.finding_id}
                        onClick={() => handleSelectFinding(finding)}
                        className={`p-3 rounded-lg border text-left cursor-pointer transition-all duration-200 hover:-translate-y-0.5 ${
                          isSelected
                            ? 'border-amber-500 bg-amber-50/40 ring-1 ring-amber-500 shadow-sm'
                            : 'border-slate-200 bg-white hover:border-slate-300 hover:shadow-sm'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2 mb-1.5">
                          <span className="font-bold text-slate-800 text-xs font-mono flex items-center gap-1.5">
                            <AlertTriangle className={`h-3.5 w-3.5 stroke-[1.5] ${
                              finding.severity === 'CRITICAL' || finding.severity === 'HIGH' ? 'text-rose-500' : 'text-amber-500'
                            }`} />
                            {finding.finding_id}
                          </span>
                          <span className={`text-[10px] uppercase font-bold shrink-0 ${severityClass}`}>
                            {finding.severity}
                          </span>
                        </div>
                        <p className="text-slate-600 text-xs line-clamp-2 leading-relaxed font-medium">
                          {finding.clause_reference || finding.discrepancy_type}: {finding.description}
                        </p>
                        <div className="mt-2 flex items-center justify-between border-t border-slate-100 pt-1.5">
                          <span className="text-[10px] text-slate-400 font-mono">
                            Rule: {finding.rule_id}
                          </span>
                          <span className="text-xs font-bold text-rose-600">
                            {Number(finding.delta) < 0 ? `-$${Math.abs(Number(finding.delta)).toLocaleString()}` : `$${Number(finding.delta).toLocaleString()}`}
                          </span>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {/* Document Viewer / Right Column */}
            <div className="lg:col-span-8 flex flex-col space-y-4">
              
              {/* Toolbar */}
              <div className="flex items-center justify-between bg-white p-3 rounded-lg border border-slate-200 shadow-sm">
                <div className="flex items-center gap-2.5 min-w-0">
                  <div className="min-w-0">
                    <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wider font-display">
                      {activeDocument?.label || 'Viewing Document'}
                    </h4>
                    <span className="text-slate-400 text-[10px] block truncate font-mono mt-0.5">
                      {activeDocument?.filename || 'No file selected'}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  {selectedFindingId && activeDocument?.type === 'contract' && (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={handleDownloadBreachPages}
                      className="px-3 py-1.5 h-8 text-[11px] font-bold uppercase tracking-wider flex items-center gap-1.5"
                    >
                      <FileDown className="h-3.5 w-3.5 stroke-[1.5]" />
                      Download Breach Pages
                    </Button>
                  )}
                  {documentUrl && (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={handleOpenFullscreen}
                      className="px-3 py-1.5 h-8 text-[11px] font-bold uppercase tracking-wider flex items-center gap-1.5"
                    >
                      <ExternalLink className="h-3.5 w-3.5 stroke-[1.5]" />
                      Open in New Tab
                    </Button>
                  )}
                </div>
              </div>

              {/* Viewer Frame */}
              <div className="h-[520px] rounded-lg border border-slate-200 bg-slate-900/5 shadow-inner overflow-hidden flex items-center justify-center relative">
                {isLoadingDocument ? (
                  <div className="absolute inset-0 bg-white/95 flex flex-col items-center justify-center p-6 z-10">
                    <div className="w-full max-w-md bg-slate-100 h-[380px] rounded-lg border border-slate-200 relative overflow-hidden flex flex-col items-center justify-center">
                      <div className="space-y-4 text-center z-10 bg-white/80 p-5 rounded-xl border border-white/40 shadow-lg max-w-xs">
                        <Spinner size="md" className="mx-auto" />
                        <div>
                          <p className="text-xs font-bold text-slate-800 uppercase tracking-wider font-display">Verifying Document Alignment</p>
                          <p className="text-[11px] text-slate-500 mt-1">Reading PDF offsets & isolating contract breach positions...</p>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : documentUrl ? (
                  <iframe
                    title="Uploaded audit file"
                    src={documentUrl}
                    className="h-full w-full bg-white border-0"
                  />
                ) : (
                  <div className="text-center p-6 space-y-3">
                    <Eye className="h-10 w-10 text-slate-300 mx-auto stroke-[1.2] animate-pulse" />
                    <div>
                      <p className="text-xs font-bold text-slate-800 uppercase tracking-wider font-display">Select a Document</p>
                      <p className="text-[11px] text-slate-400 mt-1 max-w-[200px] mx-auto">Choose a contract or invoice from the list to display its original contents.</p>
                    </div>
                  </div>
                )}
              </div>

              {/* AI Highlights & Evidence Block */}
              {selectedFinding && (
                <div className="rounded-xl border border-amber-200 bg-gradient-to-r from-amber-50 to-orange-50/20 p-4 shadow-sm relative overflow-hidden">
                  
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-amber-100 pb-3 mb-3">
                    <div className="flex items-center gap-2">
                      <div>
                        <h4 className="text-xs font-bold text-slate-900 font-display uppercase tracking-wider">
                          AI Evidence Extraction — {selectedFinding.finding_id}
                        </h4>
                        <p className="text-[10px] text-amber-800 font-semibold mt-0.5">
                          Verified Clause Reference: {selectedFinding.clause_reference || 'Not specified'}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => handleCopyText(selectedFinding.clause_text || selectedFinding.description, selectedFinding.finding_id)}
                        className="text-[10px] font-bold uppercase tracking-wider text-slate-600 hover:text-slate-900 bg-white border border-amber-200 rounded px-2.5 py-1.5 transition-colors flex items-center gap-1.5"
                      >
                        {copiedId === selectedFinding.finding_id ? (
                          <Check className="h-3 w-3 text-emerald-600" />
                        ) : (
                          <Copy className="h-3 w-3" />
                        )}
                        {copiedId === selectedFinding.finding_id ? 'Copied' : 'Copy Clause Text'}
                      </button>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <span className="text-[10px] font-bold text-amber-800 uppercase tracking-wider">
                        Quoted Contract Text
                      </span>
                      <div className="mt-1 block bg-amber-50/70 border-l-2 border-amber-400 text-slate-800 rounded px-3 py-2 text-xs font-mono leading-relaxed whitespace-pre-wrap">
                        {selectedFinding.clause_text || 'No exact clause text provided.'}
                      </div>
                    </div>

                    <div>
                      <span className="text-[10px] font-bold text-amber-800 uppercase tracking-wider">
                        Discrepancy Analysis
                      </span>
                      <p className="text-xs text-slate-700 leading-relaxed font-medium mt-1">
                        {selectedFinding.description}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}