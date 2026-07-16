import { useState } from 'react';
import { ShieldAlert, AlertTriangle, ShieldCheck, HelpCircle, FileText, FileCheck, UploadCloud } from 'lucide-react';
import { uploadContract, uploadInvoice, runAudit, predictRisk } from '../api';
import PageHeader from '../components/layout/PageHeader';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Spinner from '../components/ui/Spinner';
import Modal from '../components/ui/Modal';

function RiskBadge({ risk }) {
  if (!risk) return null;
  const config = {
    HIGH:         { color: "bg-rose-100 text-rose-800 border-rose-200",    tag: "High Risk", icon: ShieldAlert },
    MEDIUM:       { color: "bg-amber-100 text-amber-800 border-amber-200", tag: "Medium Risk", icon: AlertTriangle },
    LOW:          { color: "bg-emerald-100 text-emerald-800 border-emerald-200", tag: "Low Risk", icon: ShieldCheck },
    NEW_SUPPLIER: { color: "bg-slate-100 text-slate-600 border-slate-200",  tag: "New Supplier", icon: HelpCircle }
  }[risk.risk_level] || { color: "bg-slate-100 text-slate-600 border-slate-200",  tag: "Unknown", icon: HelpCircle };

  const Icon = config.icon;

  return (
    <div className={`mt-2 p-3 rounded-xl border text-xs ${config.color} flex items-start gap-2.5`}>
      <Icon className="h-4.5 w-4.5 stroke-[1.5] mt-0.5 shrink-0" />
      <div>
        <div className="font-bold uppercase tracking-wider mb-0.5">
          {config.tag}
        </div>
        <p className="text-xs mb-1">{risk.reason}</p>
        {risk.focus_areas && risk.focus_areas.length > 0 && (
          <p className="text-xs font-semibold">
            Focus: {risk.focus_areas.join(", ")}
          </p>
        )}
      </div>
    </div>
  );
}

export default function Upload({ onAuditStarted }) {
  const [contractFile, setContractFile] = useState(null);
  const [invoiceFiles, setInvoiceFiles] = useState([]); // Array of { file, file_id, risk, loadingRisk, error }
  const [supplierNameOverride, setSupplierNameOverride] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState('');
  const [error, setError] = useState('');
  const [dragContractActive, setDragContractActive] = useState(false);
  const [dragInvoicesActive, setDragInvoicesActive] = useState(false);
  const [duplicateAuditId, setDuplicateAuditId] = useState(null);

  const handleContractDrop = (e) => {
    e.preventDefault();
    setDragContractActive(false);
    if (e.dataTransfer.files?.[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type === 'application/pdf') { setContractFile(file); setError(''); }
      else setError('Only PDF documents are supported for contracts.');
    }
  };

  const processNewInvoices = async (files) => {
    const newItems = files.map(f => ({ file: f, file_id: null, risk: null, loadingRisk: true, error: null }));
    setInvoiceFiles(prev => [...prev, ...newItems].slice(0, 10));
    setError('');

    // Process each new file
    for (const item of newItems) {
      try {
        const uploadRes = await uploadInvoice(item.file);
        
        // Update item with file_id
        setInvoiceFiles(prev => prev.map(p => 
          p.file === item.file ? { ...p, file_id: uploadRes.file_id } : p
        ));

        // Predict risk
        const riskRes = await predictRisk({ invoice_file_id: uploadRes.file_id });
        
        setInvoiceFiles(prev => prev.map(p => 
          p.file === item.file ? { ...p, risk: riskRes, loadingRisk: false } : p
        ));
        
      } catch (err) {
        setInvoiceFiles(prev => prev.map(p => 
          p.file === item.file ? { ...p, error: err.message, loadingRisk: false } : p
        ));
      }
    }
  };

  const handleInvoicesDrop = (e) => {
    e.preventDefault();
    setDragInvoicesActive(false);
    if (e.dataTransfer.files) {
      const files = Array.from(e.dataTransfer.files).filter(f => f.type === 'application/pdf');
      if (files.length > 0) {
        processNewInvoices(files);
      } else setError('Only PDF documents are supported for invoices.');
    }
  };

  const handleInvoicesInput = (e) => {
    if (e.target.files) {
      const files = Array.from(e.target.files).filter(f => f.type === 'application/pdf');
      if (files.length > 0) {
        processNewInvoices(files);
      }
    }
  };

  const handleRunAudit = async (force = false) => {
    if (!contractFile) { setError('Please upload a supplier contract.'); return; }
    if (invoiceFiles.length === 0) { setError('Please upload at least one supplier invoice.'); return; }
    
    // Ensure all invoice files have file_id
    const readyInvoices = invoiceFiles.filter(i => i.file_id);
    if (readyInvoices.length !== invoiceFiles.length) {
      setError('Please wait for all invoices to finish uploading/analyzing.');
      return;
    }

    setIsUploading(true);
    setError('');
    try {
      setUploadProgress('Uploading contract PDF...');
      const contractRes = await uploadContract(contractFile);
      
      const invoiceIds = readyInvoices.map(i => i.file_id);
      
      setUploadProgress('Initializing audit pipeline...');
      const auditRes = await runAudit(contractRes.file_id, invoiceIds, supplierNameOverride, force);
      setIsUploading(false);
      
      if (auditRes.status === "EXISTS") {
        setDuplicateAuditId(auditRes.audit_id);
      } else {
        onAuditStarted(auditRes.audit_id);
      }
    } catch (err) {
      setIsUploading(false);
      setError(err.message || 'An error occurred during file upload');
    }
  };

  const dropzoneClass = (active) =>
    `border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all flex flex-col items-center justify-center ${
      active ? 'border-teal-500 bg-teal-50' : 'border-slate-300 bg-slate-50 hover:border-slate-400 hover:bg-white'
    }`;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <PageHeader
        title="New Compliance Audit"
        description="Upload your procurement contract and supplier invoices. Our multi-agent pipeline extracts pricing rules and flags billing leakage."
      />

      <Card className="space-y-8">
        {error && (
          <div className="bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3 rounded-xl text-sm flex items-center gap-3">
            <ShieldAlert className="h-5 w-5 text-rose-600 stroke-[1.5] shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-semibold text-slate-900">1. Supplier Contract</label>
              <span className="text-slate-500 text-xs font-mono uppercase tracking-wider">[Rates & SLA Terms]</span>
            </div>
            {!contractFile ? (
              <div
                onDragOver={e => { e.preventDefault(); setDragContractActive(true); }}
                onDragLeave={() => setDragContractActive(false)}
                onDrop={handleContractDrop}
                className={dropzoneClass(dragContractActive)}
                onClick={() => document.getElementById('contract-input').click()}
              >
                <input id="contract-input" type="file" accept=".pdf" className="hidden" onChange={e => e.target.files?.[0] && (setContractFile(e.target.files[0]), setError(''))} />
                <div className="p-3 bg-teal-50 text-teal-600 rounded-2xl mb-3">
                  <UploadCloud className="h-6 w-6 stroke-[1.5]" />
                </div>
                <span className="text-sm font-bold uppercase tracking-wider text-slate-900">Drag & drop contract PDF</span>
                <span className="text-[11px] font-semibold text-slate-500 mt-1 uppercase tracking-wider">or click to browse (max 20MB)</span>
              </div>
            ) : (
              <div className="flex items-center justify-between p-4 bg-emerald-50 border border-emerald-200 rounded-xl">
                <div className="flex items-center gap-3 truncate">
                  <div className="p-2 bg-emerald-100 text-emerald-800 rounded-lg shrink-0">
                    <FileCheck className="h-5 w-5 stroke-[1.5]" />
                  </div>
                  <div className="truncate">
                    <span className="text-xs font-bold text-emerald-800 uppercase tracking-wider">Uploaded Contract</span>
                    <span className="text-sm font-semibold text-slate-950 block truncate mt-0.5">{contractFile.name}</span>
                    <span className="text-[10px] text-slate-500 font-mono mt-0.5 block">{(contractFile.size / 1024 / 1024).toFixed(2)} MB</span>
                  </div>
                </div>
                <button type="button" onClick={() => setContractFile(null)} className="text-xs font-bold uppercase tracking-wider text-rose-600 hover:text-rose-800 px-2 py-1">Remove</button>
              </div>
            )}
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-semibold text-slate-900">2. Supplier Invoices</label>
              <span className="text-slate-500 text-xs font-mono uppercase tracking-wider">[Up to 10 PDFs]</span>
            </div>
            <div
              onDragOver={e => { e.preventDefault(); setDragInvoicesActive(true); }}
              onDragLeave={() => setDragInvoicesActive(false)}
              onDrop={handleInvoicesDrop}
              className={dropzoneClass(dragInvoicesActive)}
              onClick={() => document.getElementById('invoices-input').click()}
            >
              <input id="invoices-input" type="file" multiple accept=".pdf" className="hidden" onChange={handleInvoicesInput} />
              <div className="p-3 bg-teal-50 text-teal-600 rounded-2xl mb-3">
                <UploadCloud className="h-6 w-6 stroke-[1.5]" />
              </div>
              <span className="text-sm font-bold uppercase tracking-wider text-slate-900">Drag & drop invoice PDFs</span>
              <span className="text-[11px] font-semibold text-slate-500 mt-1 uppercase tracking-wider">or click to browse</span>
            </div>
            {invoiceFiles.length > 0 && (
              <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
                {invoiceFiles.map((item, idx) => (
                  <div key={idx} className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm flex flex-col">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 truncate">
                        <FileText className="h-4 w-4 text-slate-400 shrink-0 stroke-[1.5]" />
                        <span className="text-slate-700 truncate text-xs font-semibold font-mono">{item.file.name}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        {item.loadingRisk && <Spinner className="w-4 h-4 text-teal-600 animate-spin" />}
                        <button type="button" onClick={() => setInvoiceFiles(prev => prev.filter((_, i) => i !== idx))} className="text-[10px] font-bold uppercase tracking-wider text-rose-600 hover:text-rose-800">Remove</button>
                      </div>
                    </div>
                    {item.error && <div className="text-xs text-rose-600 mt-2">{item.error}</div>}
                    <RiskBadge risk={item.risk} />
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="border-t border-slate-200 pt-6 space-y-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">Advanced Options</h4>
          <div className="max-w-md">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-700 block mb-1.5">Override Supplier Name</label>
            <Input type="text" placeholder="Auto-extracted if left blank" value={supplierNameOverride} onChange={e => setSupplierNameOverride(e.target.value)} />
          </div>
        </div>

        <div className="border-t border-slate-200 pt-6 flex justify-end">
          <Button onClick={() => handleRunAudit(false)} disabled={isUploading || !contractFile || invoiceFiles.length === 0} size="lg" className="flex items-center gap-2 font-semibold">
            {isUploading ? (
              <>
                <Spinner className="w-4 h-4 text-white" />
                {uploadProgress}
              </>
            ) : (
              <>
                <FileCheck className="h-4.5 w-4.5 stroke-[1.5]" />
                Run Compliance Audit
              </>
            )}
          </Button>
        </div>
      </Card>

      <Modal
        open={!!duplicateAuditId}
        onClose={() => setDuplicateAuditId(null)}
        title="Audit Already Exists"
        maxWidth="max-w-md"
      >
        <div className="space-y-6">
          <p className="text-sm text-slate-600">
            You have already uploaded these exact documents and generated an audit report. 
            Would you like to open the existing report, or run a new audit from scratch?
          </p>
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={() => {
              setDuplicateAuditId(null);
              handleRunAudit(true);
            }}>
              Run Again
            </Button>
            <Button onClick={() => {
              const id = duplicateAuditId;
              setDuplicateAuditId(null);
              onAuditStarted(id);
            }}>
              Open Existing Report
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
