/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Grades vendor billing behavior.
 * 
 * What it means:
 * Vendor ranking scorecard page.
 * 
 * Importance in Project:
 * High. Simplifies procurement metrics with letter grades.
 */

import { useState, useEffect } from 'react';
import { Building2, ShieldCheck, AlertTriangle, DollarSign, ArrowUpRight, ArrowDownRight, ArrowRight, RefreshCw, ChevronRight } from 'lucide-react';
import { getSuppliers, getSupplierSummary } from '../api';
import PageHeader from '../components/layout/PageHeader';
import StatCard from '../components/ui/StatCard';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Spinner from '../components/ui/Spinner';
import EmptyState from '../components/ui/EmptyState';
import { Table, TableHead, TableBody, TableRow, TableCell } from '../components/ui/Table';

export default function SupplierScorecard({ onSelectSupplier }) {
  const [suppliers, setSuppliers] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [suppliersData, summaryData] = await Promise.all([getSuppliers(), getSupplierSummary()]);
      setSuppliers(suppliersData);
      setSummary(summaryData);
    } catch (err) {
      console.error('Error loading scorecard:', err);
      setError('Failed to load supplier risk scorecard data.');
    } finally {
      setLoading(false);
    }
  };

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { fetchData(); }, []);

  const renderTrend = (trend) => {
    if (trend === 'improving') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
          <ArrowUpRight className="h-3.5 w-3.5 stroke-[1.5]" /> Improving
        </span>
      );
    }
    if (trend === 'worsening') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
          <ArrowDownRight className="h-3.5 w-3.5 stroke-[1.5]" /> Worsening
        </span>
      );
    }
    if (trend === 'stable') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-50 text-slate-600 border border-slate-200">
          <ArrowRight className="h-3.5 w-3.5 stroke-[1.5]" /> Stable
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200 uppercase tracking-wider text-[10px]">
        New
      </span>
    );
  };

  const renderScoreBadge = (score, band) => {
    const label = band === 'green' ? 'Low Risk' : band === 'amber' ? 'Medium Risk' : 'High Risk';
    const colorClass = band === 'green' ? 'text-emerald-600' : band === 'amber' ? 'text-amber-600' : 'text-rose-600';
    const barColor = band === 'green' ? 'bg-emerald-500' : band === 'amber' ? 'bg-amber-500' : 'bg-rose-500';
    
    return (
      <div className="flex flex-col gap-1.5 min-w-[140px]">
        <div className="flex items-center justify-between text-xs font-bold">
          <span className="font-mono text-slate-800">{score.toFixed(1)}%</span>
          <span className={`text-[9px] uppercase tracking-wider ${colorClass}`}>{label}</span>
        </div>
        <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden border border-slate-200/50">
          <div 
            className={`h-full rounded-full transition-all duration-500 ${barColor}`} 
            style={{ width: `${score}%` }}
          />
        </div>
      </div>
    );
  };

  if (loading) return <div className="py-24"><Spinner label="Loading supplier scorecard..." /></div>;

  if (error) {
    return (
      <EmptyState icon={AlertTriangle} title="Error Loading Scorecard" description={error} actionLabel="Try Again" onAction={fetchData} />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Supplier Risk Scorecard"
        description="Compliance monitoring, risk banding, and billing leakage tracking across your vendor portfolio."
        actions={<Button variant="secondary" size="sm" onClick={fetchData}><RefreshCw className="h-4 w-4" /> Refresh</Button>}
      />

      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard label="Suppliers Tracked" tooltip="Total number of suppliers registered in the system." value={summary.total_suppliers_tracked} subtext="Active vendors" icon={Building2} />
          <StatCard label="Avg Compliance" tooltip="Average compliance score across all active suppliers." value={`${summary.average_score.toFixed(1)}%`} icon={ShieldCheck} iconColor="text-emerald-600" iconBg="bg-emerald-50" />
          <StatCard label="Red Zone" tooltip="Number of suppliers with an overall compliance score below 50%." value={summary.suppliers_in_red_zone} subtext="Score below 50%" icon={AlertTriangle} iconColor="text-rose-600" iconBg="bg-rose-50" />
          <StatCard label="Aggregate Leakage" tooltip="Total identified monetary leakage across all suppliers." value={`$${Math.round(parseFloat(summary.total_leakage_all_time)).toLocaleString('en-US')}`} icon={DollarSign} iconColor="text-rose-600" iconBg="bg-rose-50" />
        </div>
      )}

      <div className="card overflow-hidden p-0">
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-900">Supplier Leaderboard</h3>
          <span className="text-xs text-slate-500">Sorted by risk (riskiest first)</span>
        </div>
        {suppliers.length === 0 ? (
          <div className="py-12 text-center text-slate-500 text-sm">No supplier data yet. Complete an audit to build scorecards.</div>
        ) : (
          <Table>
            <TableHead>
              <tr>
                <TableCell header className="text-center w-12">#</TableCell>
                <TableCell header>Supplier</TableCell>
                <TableCell header>Score</TableCell>
                <TableCell header className="text-center">Trend</TableCell>
                <TableCell header className="text-center">Audits</TableCell>
                <TableCell header className="text-right">Leakage</TableCell>
                <TableCell header>Last Audit</TableCell>
                <TableCell header className="text-center">Negotiation</TableCell>
                <TableCell header className="text-center w-20" />
              </tr>
            </TableHead>
            <TableBody>
              {suppliers.map((supplier, index) => (
                <TableRow key={supplier.supplier_name} onClick={() => onSelectSupplier(supplier.supplier_name)}>
                  <TableCell className="text-center font-mono text-slate-400">{index + 1}</TableCell>
                  <TableCell className="font-semibold text-slate-900">{supplier.supplier_name}</TableCell>
                  <TableCell>{renderScoreBadge(supplier.latest_score, supplier.risk_band)}</TableCell>
                  <TableCell className="text-center">{renderTrend(supplier.trend)}</TableCell>
                  <TableCell className="text-center font-mono">{supplier.audit_count}</TableCell>
                  <TableCell className="text-right font-mono font-semibold text-rose-600">
                    ${parseFloat(supplier.total_leakage_identified).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </TableCell>
                  <TableCell className="text-slate-500 text-xs">
                    {new Date(supplier.last_audit_date).toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' })}
                  </TableCell>
                  <TableCell className="text-center">
                    {supplier.audit_count >= 2 ? (
                      <Badge variant="brand">Ready</Badge>
                    ) : (
                      <span className="text-xs text-slate-400 italic">Need 2+ audits</span>
                    )}
                  </TableCell>
                  <TableCell className="text-center text-teal-600 text-xs font-semibold">
                    View <ChevronRight className="h-4 w-4 inline" />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  );
}
