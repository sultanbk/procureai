/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Modal displaying draft dispute letters.
 * 
 * What it means:
 * Draft letter inspector.
 * 
 * Importance in Project:
 * Medium. Allows copy-pasting or saving dispute drafts.
 */

import { useEffect, useState, useMemo } from 'react';
import { jsPDF } from 'jspdf';
import { generateDisputeLetter, getDisputeLetter, reviseDisputeLetter } from '../api';
import {
  FileText, Sparkles, Smile, AlertTriangle, Printer, Edit3,
  Copy, Check, Mail, FileDown, Sliders, ChevronLeft, Scale, User
} from 'lucide-react';
import Modal from './ui/Modal';
import Button from './ui/Button';
import Spinner from './ui/Spinner';
import { useToast } from './ui/ToastProvider';

const labelClass = 'block text-xs font-semibold text-slate-700 uppercase tracking-wide';

export default function DisputeLetterModal({ isOpen, onClose, auditId, supplierName }) {
  const { toast } = useToast();
  // Step state: 'form' | 'loading' | 'preview'
  const [step, setStep] = useState('form');
  const [error, setError] = useState(null);
  const [isHydrating, setIsHydrating] = useState(false);

  // Form Fields
  const [companyName, setCompanyName] = useState('ProcureAI Analytics');
  const [signatoryName, setSignatoryName] = useState('Procurement Manager');
  const [signatoryTitle, setSignatoryTitle] = useState('Head of Procurement');
  const [supplierContact, setSupplierContact] = useState('Account Manager');
  const [supplierEmail, setSupplierEmail] = useState('');
  const [internalRef, setInternalRef] = useState('');

  // Default due date: today + 14 days
  const getDefaultDueDate = () => {
    const d = new Date();
    d.setDate(d.getDate() + 14);
    return d.toISOString().split('T')[0];
  };
  const [dueDate, setDueDate] = useState(getDefaultDueDate());

  // Result state
  const [letterText, setLetterText] = useState('');
  const [letterHtml, setLetterHtml] = useState('');
  const [copied, setCopied] = useState(false);
  const [isRevisionOpen, setIsRevisionOpen] = useState(false);
  const [revisionText, setRevisionText] = useState('');
  const [isRevising, setIsRevising] = useState(false);
  
  // Custom UI states
  const [previewTab, setPreviewTab] = useState('print'); // 'edit' | 'print'
  const [activeTone, setActiveTone] = useState(''); // 'collaborative' | 'formal' | 'strict'

  useEffect(() => {
    let ignore = false;
    if (!isOpen || !auditId) return undefined;

    setError(null);
    setIsHydrating(true);
    getDisputeLetter(auditId)
      .then((data) => {
        if (ignore) return;
        setLetterText(data.letter_text);
        setLetterHtml(data.letter_html || '');
        setStep('preview');
      })
      .catch(() => {
        if (!ignore) setStep((currentStep) => (currentStep === 'preview' ? currentStep : 'form'));
      })
      .finally(() => {
        if (!ignore) setIsHydrating(false);
      });

    return () => {
      ignore = true;
    };
  }, [auditId, isOpen]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStep('loading');
    setError(null);

    const payload = {
      audit_id: auditId,
      company_name: companyName,
      signatory_name: signatoryName,
      signatory_title: signatoryTitle,
      supplier_contact: supplierContact,
      supplier_email: supplierEmail || null,
      due_date: dueDate,
      reference_number: internalRef || null
    };

    try {
      const data = await generateDisputeLetter(payload);
      setLetterText(data.letter_text);
      setLetterHtml(data.letter_html || '');
      setStep('preview');
      setActiveTone('formal'); // Default initial tone is formal
    } catch (err) {
      setStep('form');
      setError(err.message || 'An error occurred while generating the letter.');
    }
  };

  const handleRevisionSubmit = async (e) => {
    e.preventDefault();
    if (!revisionText.trim()) return;
    setIsRevising(true);
    setError(null);

    try {
      const data = await reviseDisputeLetter({
        audit_id: auditId,
        current_letter_text: letterText,
        change_request: revisionText.trim()
      });
      setLetterText(data.letter_text);
      setLetterHtml(data.letter_html || '');
      setRevisionText('');
      setIsRevisionOpen(false);
      toast('Letter updated with your requested changes.', 'success');
    } catch (err) {
      setError(err.message || 'Failed to revise the letter.');
    } finally {
      setIsRevising(false);
    }
  };

  const handleToneChange = async (tone) => {
    setIsRevising(true);
    setError(null);
    setActiveTone(tone);
    
    let instructions = '';
    if (tone === 'collaborative') {
      instructions = 'Rewrite this dispute letter to have a collaborative, polite, and cooperative tone. We are asking for clarification on the differences and want to resolve it together. Preserve all dates, findings, amounts, and contract clause references.';
    } else if (tone === 'formal') {
      instructions = 'Rewrite this dispute letter to have a formal, official, and professional dispute notice tone. Cite contract sections clearly. Preserve all dates, findings, amounts, and contract clause references.';
    } else if (tone === 'strict') {
      instructions = 'Rewrite this dispute letter to have a strict, assertive, and legal demand tone. Set a firm 7-day deadline for response and indicate that failure to credit may result in escalation. Preserve all dates, findings, amounts, and contract clause references.';
    }

    try {
      const data = await reviseDisputeLetter({
        audit_id: auditId,
        current_letter_text: letterText,
        change_request: instructions
      });
      setLetterText(data.letter_text);
      setLetterHtml(data.letter_html || '');
      toast(`Tone switched to ${tone.toUpperCase()}`, 'success');
    } catch (err) {
      setError(err.message || `Failed to change tone to ${tone}.`);
    } finally {
      setIsRevising(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(letterText);
    setCopied(true);
    toast('Dispute letter text copied to clipboard', 'success');
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadPDF = () => {
    try {
      const doc = new jsPDF();
      doc.setFont("helvetica", "normal");
      doc.setFontSize(10.5);

      const lines = doc.splitTextToSize(letterText, 180);
      let y = 20;
      const pageHeight = doc.internal.pageSize.height;
      const margin = 15;

      lines.forEach((line) => {
        if (y > pageHeight - margin) {
          doc.addPage();
          y = 20;
        }
        doc.text(line, margin, y);
        y += 5.5; // line spacing
      });

      doc.save(`Dispute_${supplierName.replace(/\s+/g, '_')}_${auditId}.pdf`);
      toast('PDF downloaded successfully', 'success');
    } catch (err) {
      console.error("PDF generation failed:", err);
      toast('Failed to download PDF. Try copying the text instead.', 'error');
    }
  };

  // Generate Mailto Link
  const mailtoLink = `mailto:${supplierEmail || ''}?subject=${encodeURIComponent(
    `Formal Dispute — Invoice Audit Findings | ${auditId}`
  )}&body=${encodeURIComponent(letterText)}`;

  const footer =
    isHydrating ? null : step === 'form' ? (
      <Button type="submit" form="dispute-letter-form" size="lg" className="flex items-center gap-2">
        <Sparkles className="h-4 w-4 stroke-[1.5]" />
        Generate Dispute Letter
      </Button>
    ) : step === 'preview' ? (
      <div className="w-full flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <Button variant="secondary" size="sm" onClick={() => setStep('form')} className="h-9 text-[11px] font-bold uppercase tracking-wider flex items-center gap-1.5 justify-center">
          <ChevronLeft className="h-4 w-4 stroke-[1.5]" />
          Edit Form
        </Button>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" size="sm" onClick={handleCopy} className="min-w-[120px] h-9 text-[11px] font-bold uppercase tracking-wider flex items-center gap-1.5 justify-center">
            {copied ? (
              <Check className="h-3.5 w-3.5 text-emerald-600" />
            ) : (
              <Copy className="h-3.5 w-3.5 stroke-[1.5]" />
            )}
            {copied ? 'Copied!' : 'Copy Text'}
          </Button>
          <Button size="sm" onClick={downloadPDF} className="h-9 text-[11px] font-bold uppercase tracking-wider flex items-center gap-1.5 justify-center">
            <FileDown className="h-3.5 w-3.5 stroke-[1.5]" />
            Download PDF
          </Button>
          <Button variant="secondary" size="sm" onClick={() => setIsRevisionOpen((value) => !value)} className="h-9 text-[11px] font-bold uppercase tracking-wider flex items-center gap-1.5 justify-center">
            <Sparkles className="h-3.5 w-3.5 stroke-[1.5]" />
            Custom Prompts
          </Button>
          {supplierEmail && (
            <a
              href={mailtoLink}
              className="inline-flex items-center justify-center font-bold tracking-wider uppercase rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 px-4 text-xs bg-emerald-600 hover:bg-emerald-700 text-white border border-transparent shadow-sm h-9 flex items-center gap-1.5 justify-center"
            >
              <Mail className="h-3.5 w-3.5 stroke-[1.5]" />
              Draft Email
            </a>
          )}
        </div>
      </div>
    ) : null;

  // Format letter text as basic styled HTML paragraphs if letterHtml is missing
  const richHtmlContent = useMemo(() => {
    if (letterHtml) return letterHtml;
    return letterText
      .split('\n')
      .map(p => {
        const trimmed = p.trim();
        if (!trimmed) return '<div class="h-2"></div>';
        if (trimmed.startsWith('-') || trimmed.startsWith('*')) {
          return `<li class="ml-4 list-disc mb-1 text-slate-700">${trimmed.slice(1).trim()}</li>`;
        }
        return `<p class="mb-3 text-slate-700 leading-relaxed">${trimmed}</p>`;
      })
      .join('');
  }, [letterText, letterHtml]);

  return (
    <Modal
      open={isOpen}
      onClose={onClose}
      title="Generate Dispute Letter"
      footer={footer}
      maxWidth="max-w-3xl"
      flexBody={true}
    >
      {isHydrating && step !== 'preview' && (
        <div className="py-12 flex flex-col items-center justify-center flex-1">
          <Spinner label="Checking for saved dispute letter..." />
        </div>
      )}

      {step === 'form' && !isHydrating && (
        <form id="dispute-letter-form" onSubmit={handleSubmit} className="space-y-5 flex-1 overflow-y-auto pr-1 select-none">
          {error && (
            <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs font-semibold flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 shrink-0 text-rose-600" />
              <span>{error}</span>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Sender & Authority Info Card */}
            <div className="bg-slate-50/60 border border-slate-200/80 rounded-xl p-4.5 space-y-4">
              <div className="flex items-center gap-2 border-b border-slate-200/60 pb-3">
                <div className="p-1.5 bg-teal-50 border border-teal-100 rounded-lg text-teal-600">
                  <User className="h-4 w-4 stroke-[1.5]" />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Sender Profile</h3>
                  <p className="text-[10px] text-slate-400">Identify your entity & authorized signatory</p>
                </div>
              </div>

              <div className="space-y-3">
                <div className="space-y-1.5">
                  <label className={labelClass}>Your Company Name</label>
                  <input
                    type="text"
                    required
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    className="input-field"
                    placeholder="e.g. ProcureAI Analytics"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3.5">
                  <div className="space-y-1.5">
                    <label className={labelClass}>Signatory Name</label>
                    <input
                      type="text"
                      required
                      value={signatoryName}
                      onChange={(e) => setSignatoryName(e.target.value)}
                      className="input-field"
                      placeholder="e.g. Procurement Manager"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className={labelClass}>Signatory Title</label>
                    <input
                      type="text"
                      required
                      value={signatoryTitle}
                      onChange={(e) => setSignatoryTitle(e.target.value)}
                      className="input-field"
                      placeholder="e.g. Head of Procurement"
                    />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className={labelClass}>Internal Reference # (Optional)</label>
                  <input
                    type="text"
                    value={internalRef}
                    onChange={(e) => setInternalRef(e.target.value)}
                    placeholder="e.g. DISP-2026-001"
                    className="input-field"
                  />
                </div>
              </div>
            </div>

            {/* Recipient & Timeline Details Card */}
            <div className="bg-slate-50/60 border border-slate-200/80 rounded-xl p-4.5 space-y-4">
              <div className="flex items-center gap-2 border-b border-slate-200/60 pb-3">
                <div className="p-1.5 bg-sky-50 border border-sky-100 rounded-lg text-sky-600">
                  <Mail className="h-4 w-4 stroke-[1.5]" />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Recipient Details</h3>
                  <p className="text-[10px] text-slate-400">Specify supplier profile & response timeline</p>
                </div>
              </div>

              <div className="space-y-3">
                <div className="space-y-1.5">
                  <label className={labelClass}>Supplier Legal Entity</label>
                  <input
                    type="text"
                    disabled
                    value={supplierName}
                    className="input-field bg-slate-100 text-slate-500 border-slate-200 cursor-not-allowed font-medium"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3.5">
                  <div className="space-y-1.5">
                    <label className={labelClass}>Contact Person</label>
                    <input
                      type="text"
                      required
                      value={supplierContact}
                      onChange={(e) => setSupplierContact(e.target.value)}
                      className="input-field"
                      placeholder="e.g. Account Manager"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className={labelClass}>Email (Optional)</label>
                    <input
                      type="email"
                      value={supplierEmail}
                      onChange={(e) => setSupplierEmail(e.target.value)}
                      placeholder="finance@supplier.com"
                      className="input-field"
                    />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className={labelClass}>Response Due Date</label>
                  <input
                    type="date"
                    required
                    value={dueDate}
                    onChange={(e) => setDueDate(e.target.value)}
                    className="input-field"
                  />
                </div>
              </div>
            </div>
          </div>
        </form>
      )}

      {step === 'loading' && (
        <div className="py-16 flex flex-col items-center justify-center flex-1">
          <Spinner label="Drafting your dispute letter..." />
        </div>
      )}

      {step === 'preview' && (
        <div className="space-y-4 flex flex-col flex-1 min-h-0">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs font-semibold flex items-center gap-2 shrink-0">
              <AlertTriangle className="h-4 w-4 text-rose-600 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Tone Switcher & Workspace Tabs Control Panel */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-200/80 pb-4 shrink-0">
            {/* Tone Switcher */}
            <div className="flex flex-wrap items-center gap-3">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                <Sparkles className="h-3.5 w-3.5 text-teal-500 animate-pulse" />
                Tone Calibration:
              </span>
              <div className="flex gap-1.5">
                <button
                  type="button"
                  disabled={isRevising}
                  onClick={() => handleToneChange('collaborative')}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all duration-200 flex items-center gap-1.5 ${
                    activeTone === 'collaborative'
                      ? 'bg-teal-50 border border-teal-200 text-teal-800 shadow-sm'
                      : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  <Smile className="h-3.5 w-3.5 stroke-[1.5]" />
                  Collaborative
                </button>
                <button
                  type="button"
                  disabled={isRevising}
                  onClick={() => handleToneChange('formal')}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all duration-200 flex items-center gap-1.5 ${
                    activeTone === 'formal'
                      ? 'bg-slate-900 border border-slate-950 text-white shadow-sm font-medium'
                      : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  <Scale className="h-3.5 w-3.5 stroke-[1.5]" />
                  Formal Notice
                </button>
                <button
                  type="button"
                  disabled={isRevising}
                  onClick={() => handleToneChange('strict')}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all duration-200 flex items-center gap-1.5 ${
                    activeTone === 'strict'
                      ? 'bg-rose-50 border border-rose-200 text-rose-800 shadow-sm'
                      : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  <AlertTriangle className="h-3.5 w-3.5 stroke-[1.5]" />
                  Strict Demand
                </button>
              </div>
            </div>

            {/* Workspace View Mode Toggle */}
            <div className="flex items-center gap-2 shrink-0">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider hidden sm:inline">View Mode:</span>
              <div className="inline-flex p-1 bg-slate-100 rounded-lg border border-slate-200">
                <button
                  type="button"
                  onClick={() => setPreviewTab('print')}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors flex items-center gap-1.5 ${
                    previewTab === 'print'
                      ? 'bg-white text-slate-900 shadow-sm'
                      : 'text-slate-500 hover:text-slate-700'
                  }`}
                >
                  <Printer className="h-3.5 w-3.5 stroke-[1.5]" />
                  Print Layout
                </button>
                <button
                  type="button"
                  onClick={() => setPreviewTab('edit')}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors flex items-center gap-1.5 ${
                    previewTab === 'edit'
                      ? 'bg-white text-slate-900 shadow-sm'
                      : 'text-slate-500 hover:text-slate-700'
                  }`}
                >
                  <Edit3 className="h-3.5 w-3.5 stroke-[1.5]" />
                  Edit Draft
                </button>
              </div>
            </div>
          </div>

          {/* Main workspace area */}
          <div className="flex-1 min-h-0 relative">
            {isRevising && (
              <div className="absolute inset-0 bg-white/80 backdrop-blur-[1px] flex flex-col items-center justify-center z-20 rounded-md">
                <Spinner size="md" label="Recalibrating audit letter tone..." />
              </div>
            )}

            {previewTab === 'edit' ? (
              <textarea
                value={letterText}
                onChange={(e) => setLetterText(e.target.value)}
                className="absolute inset-0 w-full h-full p-4 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-mono text-xs leading-relaxed focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 resize-none shadow-inner"
              />
            ) : (
              <div className="absolute inset-0 bg-slate-100/60 border border-slate-200 rounded-xl p-5 overflow-y-auto shadow-inner scroll-smooth">
                {/* Physical Sheet Mockup */}
                <div className="bg-white shadow-xl border border-slate-200 p-8 sm:p-11 w-full max-w-xl mx-auto text-left text-[11px] text-slate-700 leading-relaxed font-sans h-fit relative rounded-sm my-2">
                  {/* Elegant top accent bar */}
                  <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-teal-500 to-emerald-600" />
                  
                  {/* Letterhead Header */}
                  <div className="flex justify-between items-start border-b border-slate-800 pb-3 mb-5">
                    <div>
                      <h2 className="text-[13px] font-bold uppercase tracking-wider text-slate-900 font-display">
                        {companyName}
                      </h2>
                      <p className="text-[9px] text-slate-400 font-semibold tracking-wide uppercase mt-0.5">Procurement Operations</p>
                    </div>
                    {internalRef && (
                      <div className="text-right text-[9px] text-slate-500 font-mono bg-slate-50 border border-slate-200/80 px-2.5 py-1 rounded">
                        REF: {internalRef}
                      </div>
                    )}
                  </div>

                  {/* Letter Content Render */}
                  <div
                    className="dispute-letter-rich-content space-y-2.5"
                    dangerouslySetInnerHTML={{ __html: richHtmlContent }}
                  />

                  {/* Signatures block */}
                  <div className="mt-8 pt-4 border-t border-slate-100 flex flex-col justify-end">
                    <p className="text-[9px] text-slate-400 uppercase tracking-wider font-bold">Authorized Signatory</p>
                    <p className="text-slate-800 font-bold text-xs mt-1">{signatoryName}</p>
                    <p className="text-slate-500 text-[10px]">{signatoryTitle}</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Prompt Instruction Revision Drawer */}
          {isRevisionOpen && (
            <form onSubmit={handleRevisionSubmit} className="rounded-xl border border-slate-200 bg-slate-50/50 p-4.5 space-y-3.5 shadow-sm shrink-0">
              <div>
                <label className={labelClass}>Custom Refinement Prompt</label>
                <p className="text-[10px] text-slate-500">Provide direct instructions to the AI agent to rewrite sections, format lists, or update references.</p>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-2">
                <input
                  type="text"
                  value={revisionText}
                  onChange={(e) => setRevisionText(e.target.value)}
                  placeholder="e.g. Add a note about contract extension review and format findings as a bulleted list"
                  className="input-field flex-1"
                  disabled={isRevising}
                />
                <Button type="submit" size="sm" disabled={isRevising || !revisionText.trim()} className="shrink-0 h-9 text-[11px] font-bold uppercase tracking-wider flex items-center gap-1.5 justify-center">
                  {isRevising ? <Spinner className="h-4 w-4" label="" /> : <Sparkles className="h-3.5 w-3.5 stroke-[1.5]" />}
                  Apply Change
                </Button>
              </div>

              {/* Template Prompt Chips */}
              <div className="flex flex-wrap gap-1.5">
                {[
                  'Summarize findings in bullets',
                  'Request a formal credit note',
                  'Make closing line more polite',
                  'Add reference to contract annex'
                ].map((chip) => (
                  <button
                    key={chip}
                    type="button"
                    disabled={isRevising}
                    onClick={() => setRevisionText(chip)}
                    className="px-2.5 py-1 text-[10px] font-semibold bg-white hover:bg-teal-50 hover:text-teal-700 hover:border-teal-200 border border-slate-200 rounded-md transition-all text-slate-500 select-none cursor-pointer"
                  >
                    + {chip}
                  </button>
                ))}
              </div>
            </form>
          )}
        </div>
      )}
    </Modal>
  );
}
