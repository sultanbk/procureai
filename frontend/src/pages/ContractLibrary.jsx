/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Displays uploaded contracts and parsed rules.
 * 
 * What it means:
 * Contract manager page.
 * 
 * Importance in Project:
 * High. Houses baseline MSA and addenda rules.
 */

import { useState, useEffect } from 'react';
import { Plus, Trash2, Calendar, FileText, RefreshCw, UploadCloud, PlusCircle, AlertCircle, Search, Filter } from 'lucide-react';
import { getContracts, registerContract, deleteContract, updateContractAliases, restoreContract } from '../api';
import PageHeader from '../components/layout/PageHeader';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Input from '../components/ui/Input';
import Spinner from '../components/ui/Spinner';
import EmptyState from '../components/ui/EmptyState';
import Modal from '../components/ui/Modal';
import { useToast } from '../components/ui/ToastProvider';
import { Table, TableHead, TableBody, TableRow, TableCell } from '../components/ui/Table';

export default function ContractLibrary({ onSelectSupplier }) {
  const { toast, confirm } = useToast();
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [showArchived, setShowArchived] = useState(false);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [supplierName, setSupplierName] = useState('');
  const [aliases, setAliases] = useState('');
  const [validFrom, setValidFrom] = useState('');
  const [validUntil, setValidUntil] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);

  const [isAliasModalOpen, setIsAliasModalOpen] = useState(false);
  const [activeContract, setActiveContract] = useState(null);
  const [newAlias, setNewAlias] = useState('');

  const [searchQuery, setSearchQuery] = useState('');
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type === 'application/pdf') {
        setSelectedFile(file);
        setUploadError(null);
      } else {
        setUploadError('Only PDF documents are supported.');
      }
    }
  };

  const dropzoneClass = (active) =>
    `border border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors flex flex-col items-center justify-center ${active
      ? 'border-teal-500 bg-teal-50/50 text-teal-600'
      : 'border-slate-300 bg-slate-50 hover:border-teal-400 hover:bg-teal-50/10'
    }`;

  const loadContracts = (archived = showArchived, isInitial = false) => {
    if (isInitial) {
      setLoading(true);
    } else {
      setIsRefreshing(true);
    }
    getContracts(archived)
      .then(data => {
        setContracts(data);
        setLoading(false);
        setIsRefreshing(false);
      })
      .catch(err => {
        setError(err.message || 'Failed to load contract library');
        setLoading(false);
        setIsRefreshing(false);
      });
  };

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { loadContracts(showArchived, true); }, []);

  const handleFileChange = (e) => {
    if (e.target.files?.[0]) setSelectedFile(e.target.files[0]);
  };

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setUploadError('Contract PDF is required.');
      return;
    }
    setUploading(true);
    setUploadError(null);
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('supplier_name', supplierName.trim());
    formData.append('supplier_aliases', aliases.trim());
    formData.append('valid_from', validFrom);
    formData.append('valid_until', validUntil);
    try {
      await registerContract(formData);
      setIsModalOpen(false);
      setSupplierName('');
      setAliases('');
      setValidFrom('');
      setValidUntil('');
      setSelectedFile(null);
      loadContracts();
      toast('Contract registered successfully', 'success');
    } catch (err) {
      setUploadError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id, permanent = false) => {
    const title = permanent ? 'Permanently delete this contract?' : 'Archive this contract?';
    const message = permanent
      ? 'This action cannot be undone. All extracted rules and metadata will be permanently deleted from the database.'
      : 'The contract will be removed from the library. Auto-audit matching for this supplier may stop.';
    const confirmLabel = permanent ? 'Delete Permanently' : 'Archive';

    const ok = await confirm({
      title,
      message,
      confirmLabel,
      variant: 'danger',
    });
    if (!ok) return;
    try {
      await deleteContract(id, permanent);
      loadContracts();
      toast(permanent ? 'Contract permanently deleted' : 'Contract archived', 'success');
    } catch (err) {
      toast(err.message || 'Delete failed', 'error');
    }
  };

  const handleRestore = async (id) => {
    try {
      await restoreContract(id);
      loadContracts();
      toast('Contract restored successfully', 'success');
    } catch (err) {
      toast(err.message || 'Restore failed', 'error');
    }
  };

  const handleOpenAliasModal = (contract) => {
    setActiveContract(contract);
    setNewAlias('');
    setIsAliasModalOpen(true);
  };

  const handleAddAlias = async (e) => {
    e.preventDefault();
    if (!newAlias.trim() || !activeContract) return;
    const updatedAliases = [...activeContract.supplier_aliases, newAlias.trim()];
    try {
      await updateContractAliases(activeContract.id, updatedAliases);
      setIsAliasModalOpen(false);
      loadContracts();
      toast('Alias added', 'success');
    } catch (err) {
      toast(err.message || 'Failed to update aliases', 'error');
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Contract Library"
        description="Store and manage legal procurement contracts to enable scheduled automatic invoice audits."
        actions={
          <Button size="sm" onClick={() => { setUploadError(null); setIsModalOpen(true); }}>
            <Plus className="h-4 w-4" /> Add Contract
          </Button>
        }
      />

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3 rounded-lg text-sm font-medium">{error}</div>
      )}

      {loading ? (
        <div className="py-24 flex justify-center"><Spinner label="Loading contract records..." /></div>
      ) : contracts.length === 0 ? (
        <EmptyState icon={FileText} title="No Contracts Registered" description="Upload a supplier contract PDF to activate auto-matching and scheduled audits." actionLabel="Upload Contract" onAction={() => setIsModalOpen(true)} />
      ) : (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-4 items-center justify-between bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <div className="relative w-full sm:max-w-xs">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-4 w-4 text-slate-400 stroke-[1.5]" />
              </span>
              <input
                type="text"
                placeholder="Search contracts or aliases..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="block w-full pl-9 pr-3 py-2 text-xs font-semibold bg-slate-50 hover:bg-slate-100/50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all text-slate-900 placeholder:text-slate-400"
              />
            </div>
            <div className="flex items-center gap-4 shrink-0">
              <label className="flex items-center gap-3 cursor-pointer select-none">
                <span className="text-xs font-semibold text-slate-600">
                  Show Archived
                </span>

                <button
                  type="button"
                  onClick={() => {
                    const newVal = !showArchived;
                    setShowArchived(newVal);
                    loadContracts(newVal, false);
                  }}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-all duration-300 ${showArchived ? "bg-teal-600" : "bg-slate-300"
                    }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white shadow-md transition-transform duration-300 ${showArchived ? "translate-x-6" : "translate-x-1"
                      }`}
                  />
                </button>
              </label>
              <div className="flex items-center gap-2 text-slate-500 text-xs font-semibold uppercase tracking-wider">
                {isRefreshing ? (
                  <RefreshCw className="h-3.5 w-3.5 text-teal-600 animate-spin" />
                ) : (
                  <Filter className="h-3.5 w-3.5" />
                )}
                <span>Showing {contracts.filter(c => {
                  const query = searchQuery.toLowerCase();
                  return c.supplier_name.toLowerCase().includes(query) ||
                    (c.original_filename && c.original_filename.toLowerCase().includes(query)) ||
                    c.supplier_aliases.some(alias => alias.toLowerCase().includes(query));
                }).length} of {contracts.length} Contracts</span>
              </div>
            </div>
          </div>

          <Card padding={false} className={isRefreshing ? "opacity-60 pointer-events-none transition-all duration-200" : "transition-all duration-200"}>
            <Table>
              <TableHead>
                <tr>
                  <TableCell header>Supplier / Vendor</TableCell>
                  <TableCell header>Version</TableCell>
                  <TableCell header>Status</TableCell>
                  <TableCell header>Supplier Aliases</TableCell>
                  <TableCell header>Validity Period</TableCell>
                  <TableCell header>Date Uploaded</TableCell>
                  <TableCell header className="text-right">Actions</TableCell>
                </tr>
              </TableHead>
              <TableBody>
                {contracts.filter(c => {
                  const query = searchQuery.toLowerCase();
                  return c.supplier_name.toLowerCase().includes(query) ||
                    (c.original_filename && c.original_filename.toLowerCase().includes(query)) ||
                    c.supplier_aliases.some(alias => alias.toLowerCase().includes(query));
                }).length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="py-8 text-center text-slate-500 italic text-sm">
                      No contracts found matching your search.
                    </TableCell>
                  </TableRow>
                ) : (
                  contracts.filter(c => {
                    const query = searchQuery.toLowerCase();
                    return c.supplier_name.toLowerCase().includes(query) ||
                      (c.original_filename && c.original_filename.toLowerCase().includes(query)) ||
                      c.supplier_aliases.some(alias => alias.toLowerCase().includes(query));
                  }).map((contract) => (
                    <TableRow key={contract.id}>
                      <TableCell className="font-semibold text-slate-900 cursor-help" title={`Original file: ${contract.original_filename || 'Unknown'}`}>
                        {contract.supplier_name}
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">v{contract.version || 1}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={
                          contract.status === 'PARSED' ? 'success' :
                            contract.status === 'FAILED' ? 'critical' :
                              'brand'
                        }>
                          {contract.status || 'PROCESSING'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1.5 max-w-xs items-center">
                          {contract.supplier_aliases.length === 0 ? (
                            <span className="text-xs text-slate-400 italic">No aliases</span>
                          ) : contract.supplier_aliases.map((a, i) => (
                            <Badge key={i} variant="default">{a}</Badge>
                          ))}
                          <button type="button" onClick={() => handleOpenAliasModal(contract)} className="text-xs font-semibold text-teal-600 hover:text-teal-700 ml-1">+ Add</button>
                        </div>
                      </TableCell>
                      <TableCell className="text-xs text-slate-600 font-medium">
                        {contract.valid_from || contract.valid_until ? (
                          <span>
                            {contract.valid_from ? new Date(contract.valid_from).toLocaleDateString() : 'Start'}
                            {' - '}
                            {contract.valid_until ? new Date(contract.valid_until).toLocaleDateString() : 'Endless'}
                          </span>
                        ) : (
                          <span className="text-slate-400 italic">Always valid</span>
                        )}
                      </TableCell>
                      <TableCell className="text-slate-600">
                        <span className="flex items-center gap-1.5">
                          <Calendar className="h-3.5 w-3.5 text-slate-400" />
                          {new Date(contract.uploaded_at).toLocaleDateString()}
                        </span>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          {contract.is_active === 0 ? (
                            <>
                              <Button variant="secondary" size="sm" onClick={() => handleRestore(contract.id)}>
                                Restore
                              </Button>
                              <Button variant="ghost" size="sm" onClick={() => handleDelete(contract.id, true)} className="text-rose-600 hover:text-rose-700 hover:bg-rose-50" title="Delete Permanently">
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </>
                          ) : (
                            <>
                              <Button variant="secondary" size="sm" onClick={() => onSelectSupplier?.(contract.supplier_name)}>View Audits</Button>
                              <Button variant="ghost" size="sm" onClick={() => handleDelete(contract.id, false)} className="text-rose-600 hover:text-rose-700 hover:bg-rose-50" title="Archive Contract">
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </Card>
        </div>
      )}

      <Modal open={isModalOpen} onClose={() => setIsModalOpen(false)} title="Add Supplier Contract" maxWidth="max-w-lg"
        footer={
          <Button onClick={(e) => { e.preventDefault(); document.getElementById('contract-upload-form')?.requestSubmit(); }} disabled={uploading}>
            {uploading ? <><RefreshCw className="h-4 w-4 animate-spin" /> Registering...</> : 'Register Contract'}
          </Button>
        }
      >
        <form id="contract-upload-form" onSubmit={handleUploadSubmit} className="space-y-4">
          {uploadError && (
            <div className="bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3 rounded-lg text-sm flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0" /><span>{uploadError}</span>
            </div>
          )}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700 uppercase tracking-wide block">Supplier Name (Optional)</label>
            <Input type="text" value={supplierName} onChange={(e) => setSupplierName(e.target.value)} placeholder="e.g. Apex Logistics Ltd (will be extracted automatically if blank)" />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700 uppercase tracking-wide block">Aliases (comma-separated)</label>
            <Input type="text" value={aliases} onChange={(e) => setAliases(e.target.value)} placeholder="e.g. Apex, Apex Ltd" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700 uppercase tracking-wide block">Valid From</label>
              <Input type="date" value={validFrom} onChange={(e) => setValidFrom(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700 uppercase tracking-wide block">Valid Until</label>
              <Input type="date" value={validUntil} onChange={(e) => setValidUntil(e.target.value)} />
            </div>
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700 uppercase tracking-wide block">Contract Document (PDF)</label>
            <div
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              onClick={() => document.getElementById('contract-file-input').click()}
              className={dropzoneClass(dragActive)}
            >
              <UploadCloud className={`h-9 w-9 mb-2 transition-colors ${dragActive ? 'text-teal-600' : 'text-slate-400 group-hover:text-teal-600'}`} />
              <span className="text-sm text-slate-900 font-semibold">{selectedFile ? selectedFile.name : 'Drag & drop PDF here, or click to browse'}</span>
              <span className="text-xs text-slate-500 mt-1">{selectedFile ? `${(selectedFile.size / 1024 / 1024).toFixed(2)} MB` : 'PDF only, up to 20MB'}</span>
              <input id="contract-file-input" type="file" accept=".pdf" onChange={handleFileChange} className="hidden" />
            </div>
          </div>
        </form>
      </Modal>

      <Modal open={isAliasModalOpen && !!activeContract} onClose={() => setIsAliasModalOpen(false)} title="Add Supplier Alias" maxWidth="max-w-sm"
        footer={<Button onClick={(e) => { e.preventDefault(); document.getElementById('alias-form')?.requestSubmit(); }}><PlusCircle className="h-4 w-4" /> Save Alias</Button>}
      >
        <form id="alias-form" onSubmit={handleAddAlias} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700 uppercase tracking-wide block">
              New alias for {activeContract?.supplier_name}
            </label>
            <Input type="text" required value={newAlias} onChange={(e) => setNewAlias(e.target.value)} placeholder="e.g. APEX CORP" />
          </div>
        </form>
      </Modal>
    </div>
  );
}
