/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Table highlighting billing errors and rate gaps.
 * 
 * What it means:
 * Audit audit table.
 * 
 * Importance in Project:
 * Critical. Central table display for audit reports.
 */

import { Fragment, useState } from 'react';
import { ChevronDown, Search, AlertCircle, Filter } from 'lucide-react';
import EvidenceBlock from './EvidenceBlock';
import Card from './ui/Card';
import Badge, { severityVariant } from './ui/Badge';
import Input from './ui/Input';
import Select from './ui/Select';

export default function DiscrepancyTable({ discrepancies }) {
  const [expandedRows, setExpandedRows] = useState({});
  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [typeFilter, setTypeFilter] = useState('ALL');

  const filteredDiscrepancies = discrepancies.filter(d => {
    const matchesSearch =
      d.invoice_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      d.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      d.clause_reference.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesSearch &&
      (severityFilter === 'ALL' || d.severity === severityFilter) &&
      (typeFilter === 'ALL' || d.discrepancy_type === typeFilter);
  });

  const uniqueTypes = [...new Set(discrepancies.map(d => d.discrepancy_type))];

  return (
    <Card className="space-y-5">
      <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4 border-b border-slate-200 pb-4">
        <div>
          <h3 className="text-base font-display font-bold text-slate-900 flex items-center gap-2">
            Audit Findings
            <Badge variant="brand">{filteredDiscrepancies.length} Flagged</Badge>
          </h3>
          <p className="text-slate-500 text-xs mt-1">Expand rows to inspect contract clauses and remediation plans.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex-1 md:w-48">
            <Input icon={Search} type="text" placeholder="Search findings..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} />
          </div>
          <Filter className="h-4 w-4 text-slate-400 hidden md:block stroke-[1.5]" />
          <Select value={severityFilter} onChange={e => setSeverityFilter(e.target.value)} className="w-auto">
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
          </Select>
          <Select value={typeFilter} onChange={e => setTypeFilter(e.target.value)} className="w-auto">
            <option value="ALL">All Types</option>
            {uniqueTypes.map(t => <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>)}
          </Select>
        </div>
      </div>

      <div className="overflow-x-auto rounded-lg border border-slate-200">
        <table className="w-full text-sm text-left">
          <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold uppercase tracking-wide text-slate-500">
            <tr>
              <th className="py-3 px-4 w-10" />
              <th className="py-3 px-4">Invoice</th>
              <th className="py-3 px-4">Line</th>
              <th className="py-3 px-4">Type</th>
              <th className="py-3 px-4">Severity</th>
              <th className="py-3 px-4 text-right">Expected / Charged</th>
              <th className="py-3 px-4 text-right">Leakage</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {filteredDiscrepancies.length === 0 ? (
              <tr>
                <td colSpan="7" className="py-12 text-center text-slate-500 text-sm">
                  <AlertCircle className="h-8 w-8 mx-auto mb-2 text-slate-300 stroke-[1.5]" />
                  No discrepancies match your filters.
                </td>
              </tr>
            ) : filteredDiscrepancies.map(d => {
              const isExpanded = !!expandedRows[d.finding_id];
              return (
                <Fragment key={d.finding_id}>
                  <tr className={`table-row-hover cursor-pointer ${isExpanded ? 'bg-teal-50/50' : ''}`} onClick={() => setExpandedRows(prev => ({ ...prev, [d.finding_id]: !prev[d.finding_id] }))}>
                    <td className="py-3 px-4 text-center">
                      <ChevronDown className={`h-4 w-4 text-slate-400 inline transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`} />
                    </td>
                    <td className="py-3 px-4 font-semibold text-slate-900">{d.invoice_id}</td>
                    <td className="py-3 px-4 font-mono text-xs text-slate-500">{d.line_id}</td>
                    <td className="py-3 px-4"><Badge variant="brand">{d.discrepancy_type.replace(/_/g, ' ')}</Badge></td>
                    <td className="py-3 px-4"><Badge variant={severityVariant(d.severity)}>{d.severity}</Badge></td>
                    <td className="py-3 px-4 text-right text-xs">
                      <span className="font-mono text-emerald-600">${parseFloat(d.unit_price_expected).toFixed(2)}</span>
                      <span className="text-slate-300 mx-1">/</span>
                      <span className="font-mono text-rose-600">${parseFloat(d.unit_price_charged).toFixed(2)}</span>
                    </td>
                    <td className="py-3 px-4 text-right font-mono font-bold text-rose-600 text-xs">
                      -${parseFloat(Math.abs(d.delta)).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </td>
                  </tr>
                  {isExpanded && (
                    <tr className="bg-slate-50">
                      <td colSpan="7" className="px-4 py-4">
                        <EvidenceBlock finding={d} />
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
