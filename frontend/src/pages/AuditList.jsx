/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Displays past invoice audits, leakage sums, and score counts.
 * 
 * What it means:
 * Audit history register page.
 * 
 * Importance in Project:
 * High. The primary table to inspect previous supplier reviews.
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { getAudits, deleteAudit } from '../api';
import { Plus, Trash2, Eye, Calendar, RefreshCw, ShieldCheck, FileBarChart, ShieldAlert, Search } from 'lucide-react';
import PageHeader from '../components/layout/PageHeader';
import StatCard from '../components/ui/StatCard';
import EmptyState from '../components/ui/EmptyState';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Spinner from '../components/ui/Spinner';
import Input from '../components/ui/Input';
import Select from '../components/ui/Select';
import { useToast } from '../components/ui/ToastProvider';
import { Table, TableHead, TableBody, TableRow, TableCell } from '../components/ui/Table';

export default function AuditList({ onSelectAudit, onNewAudit }) {
  const { toast, confirm } = useToast();
  const [audits, setAudits] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  const fetchList = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await getAudits();
      setAudits(data);
      setError('');
    } catch {
      setError('Failed to fetch audits list. Make sure the backend API server is running.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;
    const loadInitialAudits = async () => {
      try {
        const data = await getAudits();
        if (!isMounted) return;
        setAudits(data);
        setError('');
      } catch {
        if (!isMounted) return;
        setError('Failed to fetch audits list. Make sure the backend API server is running.');
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };
    void loadInitialAudits();
    return () => { isMounted = false; };
  }, []);

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    const ok = await confirm({
      title: 'Delete audit record?',
      message: 'This action cannot be undone. The audit report and all associated data will be removed.',
      confirmLabel: 'Delete',
      variant: 'danger',
    });
    if (!ok) return;
    try {
      await deleteAudit(id);
      setAudits(prev => prev.filter(a => a.audit_id !== id));
      toast('Audit record deleted', 'success');
    } catch {
      toast('Failed to delete audit', 'error');
    }
  };

  const filteredAudits = useMemo(() => {
    return audits.filter(a => {
      const matchesSearch =
        !searchTerm ||
        a.supplier_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        a.audit_id?.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = statusFilter === 'ALL' || a.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [audits, searchTerm, statusFilter]);

  const completedAudits = audits.filter(a => a.status === 'COMPLETE');
  const totalLeakage = completedAudits.reduce((acc, curr) => {
    return acc + Math.abs(parseFloat(curr.total_leakage) || 0);
  }, 0);

  const averageCompliance = completedAudits.length > 0
    ? (() => {
        let totalLines = 0;
        let compliantLines = 0;
        completedAudits.forEach(a => {
          if (a.total_lines_audited !== undefined && a.compliant_lines !== undefined) {
            totalLines += a.total_lines_audited;
            compliantLines += a.compliant_lines;
          }
        });
        if (totalLines > 0) return Math.round((compliantLines / totalLines) * 100);
        const perfectAudits = completedAudits.filter(a => (parseFloat(a.total_leakage) || 0) === 0).length;
        return Math.round((perfectAudits / completedAudits.length) * 100) || 100;
      })()
    : 100;

  const getStatusVariant = (status) => {
    if (status === 'COMPLETE') return 'success';
    if (status === 'FAILED') return 'critical';
    if (status === 'PENDING' || status.includes('_')) return 'brand';
    return 'default';
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Audit History"
        description="Browse compliance reports, leakage summaries, and active document runs."
        actions={
          <>
            <Button variant="secondary" size="sm" onClick={fetchList} disabled={isLoading} title="Refresh" className="flex items-center justify-center p-2">
              <RefreshCw className={`h-4 w-4 stroke-[1.5] ${isLoading ? 'animate-spin' : ''}`} />
            </Button>
            <Button size="sm" onClick={onNewAudit} className="flex items-center gap-1.5 font-semibold">
              <Plus className="h-4 w-4 stroke-[1.5]" /> New Audit
            </Button>
          </>
        }
      />

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3 rounded-lg text-sm flex justify-between items-center">
          <span>{error}</span>
          <button type="button" onClick={fetchList} className="font-semibold text-rose-600 hover:text-rose-800">Retry</button>
        </div>
      )}

      {!isLoading && audits.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatCard label="Total Audits" value={`${audits.length} runs`} icon={FileBarChart} iconColor="text-slate-600" iconBg="bg-slate-50" />
          <StatCard label="Compliance Index" value={`${averageCompliance}%`} subtext="Billing compliance" icon={ShieldCheck} iconColor="text-emerald-600" iconBg="bg-emerald-50" />
          <StatCard label="Recoverable Overcharges" value={`$${totalLeakage.toLocaleString('en-US')}`} icon={ShieldAlert} iconColor="text-rose-600" iconBg="bg-rose-50" />
        </div>
      )}

      {isLoading ? (
        <div className="py-24"><Spinner label="Loading audit records..." /></div>
      ) : audits.length === 0 ? (
        <EmptyState
          icon={ShieldCheck}
          title="No audits run yet"
          description="Upload your first supplier contract and invoices to check billing compliance."
          actionLabel="Launch Audit"
          onAction={onNewAudit}
        />
      ) : (
        <>
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1 max-w-md">
              <Input icon={Search} type="text" placeholder="Search by supplier or audit ID..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} />
            </div>
            <Select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="w-full sm:w-44">
              <option value="ALL">All statuses</option>
              <option value="COMPLETE">Complete</option>
              <option value="FAILED">Failed</option>
              <option value="PENDING">Pending</option>
            </Select>
          </div>
          <Table>
            <TableHead>
              <tr>
                <TableCell header>Supplier</TableCell>
                <TableCell header>Audit ID</TableCell>
                <TableCell header>Date</TableCell>
                <TableCell header>Status</TableCell>
                <TableCell header className="text-right">Leakage</TableCell>
                <TableCell header className="text-center w-28">Actions</TableCell>
              </tr>
            </TableHead>
            <TableBody>
              {filteredAudits.length === 0 ? (
                <tr>
                  <TableCell colSpan={6} className="text-center py-10 text-slate-500 text-sm">
                    No audits match your search.
                  </TableCell>
                </tr>
              ) : filteredAudits.map(a => (
                <TableRow key={a.audit_id} onClick={() => onSelectAudit(a.audit_id, a.status)}>
                  <TableCell className="font-semibold text-slate-900">{a.supplier_name}</TableCell>
                  <TableCell className="font-mono text-xs text-slate-500">{a.audit_id}</TableCell>
                  <TableCell>
                    <span className="flex items-center gap-1.5 text-slate-600">
                      <Calendar className="h-3.5 w-3.5 text-slate-400 stroke-[1.5]" />
                      {new Date(a.created_at).toLocaleDateString()}
                    </span>
                  </TableCell>
                  <TableCell>
                    <Badge variant={getStatusVariant(a.status)}>{a.status.replace(/_/g, ' ')}</Badge>
                  </TableCell>
                  <TableCell className="text-right font-mono font-semibold">
                    {a.status === 'COMPLETE' && a.total_leakage !== null ? (
                      <span className={Math.abs(parseFloat(a.total_leakage)) > 0 ? 'text-rose-600' : 'text-emerald-600'}>
                        ${Math.abs(parseFloat(a.total_leakage)).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                      </span>
                    ) : (
                      <span className="text-slate-300">—</span>
                    )}
                  </TableCell>
                  <TableCell className="text-center">
                    <div className="flex items-center justify-center gap-1">
                      <button type="button" onClick={() => onSelectAudit(a.audit_id, a.status)} className="p-1.5 rounded-lg text-slate-400 hover:text-teal-600 hover:bg-teal-50 border border-transparent hover:border-slate-200 transition-all duration-200" title="View">
                        <Eye className="h-4 w-4 stroke-[1.5]" />
                      </button>
                      <button type="button" onClick={(e) => handleDelete(e, a.audit_id)} className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 border border-transparent hover:border-slate-200 transition-all duration-200" title="Delete">
                        <Trash2 className="h-4 w-4 stroke-[1.5]" />
                      </button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </>
      )}
    </div>
  );
}
