/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Controls the automated folder monitoring system.
 * 
 * What it means:
 * Directory watcher dashboard page.
 * 
 * Importance in Project:
 * Medium. Enables watchers and views watched invoices.
 */

import { useState, useEffect } from 'react';
import { Eye, Pause, Play, RefreshCw, AlertTriangle, CheckCircle, Clock, ExternalLink, HelpCircle, FileText, ArrowRight } from 'lucide-react';
import { getWatcherStatus, pauseWatcher, resumeWatcher, getWatcherHistory, getUnmatchedFiles, getContracts, retryUnmatched } from '../api';
import PageHeader from '../components/layout/PageHeader';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Select from '../components/ui/Select';
import Spinner from '../components/ui/Spinner';
import { Table, TableHead, TableBody, TableRow, TableCell } from '../components/ui/Table';
import { useToast } from '../components/ui/ToastProvider';

export default function AutoAudit({ onSelectAudit, onGoToLibrary }) {
  const { toast } = useToast();
  const [status, setStatus] = useState({ watching: false, watch_dir: '', queue_count: 0 });
  const [history, setHistory] = useState([]);
  const [unmatched, setUnmatched] = useState([]);
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(true);

  // Selection states for manual matching
  const [selectedContractMap, setSelectedContractMap] = useState({}); // filename -> contractId
  const [retryingMap, setRetryingMap] = useState({}); // filename -> boolean

  const loadWatcherData = async () => {
    try {
      const statusRes = await getWatcherStatus();
      setStatus(statusRes);

      const historyRes = await getWatcherHistory();
      setHistory(historyRes);

      const unmatchedRes = await getUnmatchedFiles();
      setUnmatched(unmatchedRes);

      const contractsRes = await getContracts();
      setContracts(contractsRes);

      setLoading(false);
    } catch (err) {
      console.error("Failed to load Auto-Audit watcher data:", err);
      setLoading(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadWatcherData();
    // Poll every 5 seconds
    const interval = setInterval(loadWatcherData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handlePause = async () => {
    try {
      const data = await pauseWatcher();
      setStatus(prev => ({ ...prev, watching: data.watching }));
    } catch (err) {
      toast('Failed to pause watcher: ' + err.message, 'error');
    }
  };

  const handleResume = async () => {
    try {
      const data = await resumeWatcher();
      setStatus(prev => ({ ...prev, watching: data.watching }));
      loadWatcherData();
    } catch (err) {
      toast('Failed to resume watcher: ' + err.message, 'error');
    }
  };

  const handleManualMatch = async (filename) => {
    const contractId = selectedContractMap[filename];
    if (!contractId) {
      toast('Please select a contract first.', 'error');
      return;
    }

    setRetryingMap(prev => ({ ...prev, [filename]: true }));
    try {
      const res = await retryUnmatched(filename, contractId);
      if (res.success) {
        toast('Invoice audited and matched. Audit ID: ' + res.audit_id, 'success');
        loadWatcherData();
      } else {
        toast('Audit failed: ' + res.error, 'error');
      }
    } catch (err) {
      toast('Match retry failed: ' + err.message, 'error');
    } finally {
      setRetryingMap(prev => ({ ...prev, [filename]: false }));
    }
  };

  const handleContractSelect = (filename, contractId) => {
    setSelectedContractMap(prev => ({ ...prev, [filename]: contractId }));
  };

  const getStatusVariant = (itemStatus) => {
    if (itemStatus === 'COMPLETE') return 'success';
    if (itemStatus === 'UNMATCHED') return 'high';
    return 'critical';
  };

  // Group queue files: those with status MATCHING or PROCESSING
  const queueFiles = history.filter(h => ['MATCHING', 'PROCESSING', 'PENDING'].includes(h.status));
  const finishedHistory = history.filter(h => !['MATCHING', 'PROCESSING', 'PENDING'].includes(h.status));

  return (
    <div className="space-y-6">
      <PageHeader
        title="Scheduled Auto-Audit"
        description="Monitor the folder-watcher system that automatically triggers compliance audits when new invoice PDFs arrive."
        actions={
          <Button variant="secondary" size="sm" onClick={loadWatcherData}>
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        }
      />

      {loading ? (
        <div className="py-24 flex justify-center">
          <Spinner className="h-8 w-8" label="Loading status indicators..." />
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Left Column: Watcher Controls & Instructions */}
          <div className="lg:col-span-1 space-y-6">

            {/* Status Card */}
            <Card className="space-y-4">
              <div className="flex justify-between items-start">
                <div className="space-y-1">
                  <span className="text-xs text-slate-500 uppercase font-semibold tracking-wide block">Observer Mode</span>
                  <div className="flex items-center gap-2.5">
                    <span className="relative flex h-3 w-3">
                      <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                        status.watching ? 'bg-emerald-400' : 'bg-amber-400'
                      }`}></span>
                      <span className={`relative inline-flex rounded-full h-3 w-3 ${
                        status.watching ? 'bg-emerald-500' : 'bg-amber-500'
                      }`}></span>
                    </span>
                    <span className="text-base font-semibold text-slate-900">
                      {status.watching ? 'Watching Live' : 'Watcher Paused'}
                    </span>
                  </div>
                </div>

                <div className="p-2 bg-teal-50 text-teal-600 border border-teal-100 rounded-lg">
                  <Eye className="h-5 w-5" />
                </div>
              </div>

              <div className="bg-slate-50 rounded-lg p-3.5 border border-slate-200 text-xs text-slate-600 space-y-1 max-w-full">
                <span className="font-semibold uppercase tracking-wide block text-slate-700">Watch Directory:</span>
                <span className="font-mono text-slate-800 select-all block whitespace-pre-wrap leading-relaxed">{status.watch_dir}</span>
              </div>

              <div className="flex gap-3 pt-2">
                {status.watching ? (
                  <Button
                    variant="secondary"
                    className="flex-1 bg-amber-50 hover:bg-amber-100 text-amber-700 border-amber-200"
                    onClick={handlePause}
                  >
                    <Pause className="h-4 w-4" />
                    Pause Watcher
                  </Button>
                ) : (
                  <Button
                    variant="secondary"
                    className="flex-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border-emerald-200"
                    onClick={handleResume}
                  >
                    <Play className="h-4 w-4" />
                    Resume Watcher
                  </Button>
                )}
              </div>
            </Card>

            {/* Setup Guide */}
            <Card
              header={
                <h3 className="text-xs font-semibold text-slate-900 flex items-center gap-2 uppercase tracking-wide">
                  <HelpCircle className="h-4 w-4 text-teal-600 stroke-[1.5]" />
                  Auto-Audit Setup Blueprint
                </h3>
              }
            >
              <div className="relative pl-6 space-y-6 text-sm">
                {/* Vertical connecting line */}
                <div className="absolute left-2.5 top-2 bottom-2 w-0.5 border-l border-dashed border-slate-300" />

                <div className="relative flex items-start gap-3">
                  <span className="absolute -left-8 flex items-center justify-center h-5 w-5 rounded-full bg-teal-100 text-[10px] font-bold text-teal-800 border border-teal-300 shadow-sm shrink-0">
                    1
                  </span>
                  <div>
                    <p className="font-bold text-slate-800">Seed Contract Library</p>
                    <p className="text-xs text-slate-500 mt-1">Ensure the contract exists in the Contract Library to enable supplier alias matching.</p>
                  </div>
                </div>

                <div className="relative flex items-start gap-3">
                  <span className="absolute -left-8 flex items-center justify-center h-5 w-5 rounded-full bg-teal-100 text-[10px] font-bold text-teal-800 border border-teal-300 shadow-sm shrink-0">
                    2
                  </span>
                  <div className="max-w-full">
                    <p className="font-bold text-slate-800">Drop Invoice PDFs</p>
                    <p className="text-xs text-slate-500 mt-1">
                      Drop invoice files into the watch folder:
                      <span className="font-mono text-teal-600 block bg-slate-50 px-2 py-1 rounded border border-slate-200 select-all mt-1 truncate">
                        watched_invoices/
                      </span>
                    </p>
                  </div>
                </div>

                <div className="relative flex items-start gap-3">
                  <span className="absolute -left-8 flex items-center justify-center h-5 w-5 rounded-full bg-teal-100 text-[10px] font-bold text-teal-800 border border-teal-300 shadow-sm shrink-0">
                    3
                  </span>
                  <div>
                    <p className="font-bold text-slate-800">Automatic Processing</p>
                    <p className="text-xs text-slate-500 mt-1">The engine detects the file, extracts the supplier name, runs the audit, and pushes findings to notifications.</p>
                  </div>
                </div>
              </div>
            </Card>

          </div>

          {/* Right Column: Processing Queue & History */}
          <div className="lg:col-span-2 space-y-6">

            {/* Processing Queue */}
            {queueFiles.length > 0 && (
              <Card
                header={
                  <h3 className="text-xs font-semibold text-slate-900 flex items-center gap-2 uppercase tracking-wide">
                    <Clock className="h-4 w-4 text-teal-600 animate-spin" style={{ animationDuration: '3s' }} />
                    Processing Queue ({queueFiles.length})
                  </h3>
                }
              >
                <div className="divide-y divide-slate-100 text-sm">
                  {queueFiles.map((file, idx) => (
                    <div key={idx} className="py-3 flex justify-between items-center first:pt-0 last:pb-0">
                      <div>
                        <p className="font-semibold text-slate-900">{file.filename}</p>
                        <p className="text-xs text-slate-500 mt-0.5">
                          Detected: {new Date(file.detected_at).toLocaleTimeString()} • Matched Supplier: {file.supplier_name_extracted || 'Extracting...'}
                        </p>
                      </div>
                      <Badge variant="brand">{file.status}</Badge>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Unmatched Files */}
            {unmatched.length > 0 && (
              <Card className="border-rose-200 bg-rose-50/30">
                <div className="flex items-center gap-2 pb-4 mb-4 border-b border-rose-200">
                  <AlertTriangle className="h-4 w-4 text-rose-600" />
                  <h3 className="text-xs font-semibold text-rose-700 uppercase tracking-wide">
                    Unmatched Invoices ({unmatched.length})
                  </h3>
                </div>

                <div className="divide-y divide-rose-100 text-sm space-y-3">
                  {unmatched.map((file, idx) => (
                    <div key={idx} className="py-3 flex flex-col md:flex-row md:justify-between md:items-center gap-3 first:pt-0 last:pb-0">
                      <div>
                        <p className="font-semibold text-slate-900 flex items-center gap-1.5">
                          <FileText className="h-4 w-4 text-slate-400" />
                          <span>{file.filename}</span>
                        </p>
                        <p className="text-xs text-slate-500 mt-0.5">
                          Detected: {new Date(file.detected_at).toLocaleString()} • Extracted Vendor Name:{' '}
                          <span className="text-rose-700 font-semibold">&quot;{file.supplier_name_extracted}&quot;</span>
                        </p>
                      </div>

                      {contracts.length === 0 ? (
                        <Button variant="ghost" size="sm" onClick={onGoToLibrary} className="text-teal-600">
                          Seed library first
                          <ArrowRight className="h-3.5 w-3.5" />
                        </Button>
                      ) : (
                        <div className="flex items-center gap-2 flex-wrap">
                          <Select
                            onChange={(e) => handleContractSelect(file.filename, e.target.value)}
                            value={selectedContractMap[file.filename] || ''}
                            className="text-xs py-1.5"
                          >
                            <option value="">Select Contract...</option>
                            {contracts.map(c => (
                              <option key={c.id} value={c.id}>{c.supplier_name} ({c.id})</option>
                            ))}
                          </Select>
                          <Button
                            size="sm"
                            onClick={() => handleManualMatch(file.filename)}
                            disabled={retryingMap[file.filename] || !selectedContractMap[file.filename]}
                          >
                            {retryingMap[file.filename] ? 'Auditing...' : 'Match & Audit'}
                          </Button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Audit History List */}
            <Card
              header={
                <h3 className="text-xs font-semibold text-slate-900 flex items-center gap-2 uppercase tracking-wide">
                  <CheckCircle className="h-4 w-4 text-teal-600" />
                  Auto-Audit Execution Logs
                </h3>
              }
            >
              {finishedHistory.length === 0 ? (
                <p className="text-sm text-slate-500 text-center py-6">No historical auto-triggered audits run yet.</p>
              ) : (
                <Table>
                  <TableHead>
                    <tr>
                      <TableCell header>Invoice File</TableCell>
                      <TableCell header>Detected Time</TableCell>
                      <TableCell header>Supplier Found</TableCell>
                      <TableCell header>Status</TableCell>
                      <TableCell header className="text-right">Audit</TableCell>
                    </tr>
                  </TableHead>
                  <TableBody>
                    {finishedHistory.map((item) => (
                      <TableRow key={item.id}>
                        <TableCell className="font-mono text-xs max-w-[150px] truncate" title={item.filename}>
                          {item.filename}
                        </TableCell>
                        <TableCell className="text-slate-500 text-xs">
                          {new Date(item.detected_at).toLocaleString()}
                        </TableCell>
                        <TableCell>
                          {item.supplier_name_extracted || 'Unknown'}
                        </TableCell>
                        <TableCell>
                          <Badge variant={getStatusVariant(item.status)}>{item.status}</Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          {item.status === 'COMPLETE' && item.audit_id ? (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => onSelectAudit && onSelectAudit(item.audit_id, 'COMPLETE')}
                              className="text-teal-600 hover:text-teal-700"
                            >
                              Report
                              <ExternalLink className="h-3 w-3" />
                            </Button>
                          ) : (
                            <span className="text-xs text-slate-400">-</span>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </Card>

          </div>

        </div>
      )}
    </div>
  );
}
