/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Lists supplier-specific invoices and leakage audits.
 * 
 * What it means:
 * Vendor performance logs page.
 * 
 * Importance in Project:
 * High. Detailed history view for single vendors.
 */

import { useState, useEffect } from 'react';
import { ArrowLeft, Calendar, AlertCircle, FileText, RefreshCw, TrendingUp, Award } from 'lucide-react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine } from 'recharts';
import { getSupplierHistory, generateNegotiationBrief, getBriefs, getBrief } from '../api';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Card from '../components/ui/Card';
import Spinner from '../components/ui/Spinner';
import NegotiationBriefCard from '../components/NegotiationBriefCard';
import { Table, TableHead, TableBody, TableRow, TableCell } from '../components/ui/Table';
import { CHART_GRID, CHART_AXIS, CHART_COLORS } from '../utils/chartTheme';

export default function SupplierHistory({ supplierName, onBack, backLabel = 'Back to Scorecard', onSelectAudit }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [briefLoading, setBriefLoading] = useState(false);
  const [activeBrief, setActiveBrief] = useState(null);

  const fetchBriefs = async () => {
    try {
      const briefs = await getBriefs(supplierName);
      if (briefs.length > 0) {
        const latestBriefId = briefs[0].brief_id;
        const fullBrief = await getBrief(supplierName, latestBriefId);
        setActiveBrief(fullBrief);
      }
    } catch (err) {
      console.error('Error fetching briefs:', err);
    }
  };

  const handleGenerateBrief = async () => {
    setBriefLoading(true);
    try {
      const brief = await generateNegotiationBrief(supplierName);
      setActiveBrief(brief);
    } catch (err) {
      console.error('Error generating brief:', err);
    } finally {
      setBriefLoading(false);
    }
  };

  const fetchHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await getSupplierHistory(supplierName));
    } catch (err) {
      console.error('Error loading supplier history:', err);
      setError('Failed to load supplier audit history.');
    } finally {
      setLoading(false);
    }
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (supplierName) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      fetchHistory();
      fetchBriefs();
    }
  }, [supplierName]);

  const getRiskDetails = (score) => {
    if (score >= 80) return { variant: 'success', label: 'Low Risk' };
    if (score >= 50) return { variant: 'high', label: 'Medium Risk' };
    return { variant: 'critical', label: 'High Risk' };
  };

  if (loading) return <div className="py-24"><Spinner label={`Loading history for ${supplierName}...`} /></div>;

  if (error || !data) {
    return (
      <div className="text-center py-16 space-y-4">
        <AlertCircle className="h-8 w-8 text-rose-500 mx-auto" />
        <p className="text-slate-600">{error || 'No data available.'}</p>
        <div className="flex justify-center gap-2">
          <Button variant="secondary" size="sm" onClick={onBack}><ArrowLeft className="h-4 w-4" /> {backLabel}</Button>
          <Button size="sm" onClick={fetchHistory}><RefreshCw className="h-4 w-4" /> Retry</Button>
        </div>
      </div>
    );
  }

  const { history, score_history } = data;
  const currentScore = history[0]?.score ?? 100;
  const riskDetails = getRiskDetails(currentScore);

  return (
    <div className="space-y-6">
      <div>
        <Button variant="ghost" size="sm" onClick={onBack} className="mb-4">
          <ArrowLeft className="h-4 w-4" /> {backLabel}
        </Button>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-6">
          <div>
            <Badge variant="brand" className="mb-2">Supplier Risk Profile</Badge>
            <h1 className="text-2xl font-display font-bold text-slate-900">{supplierName}</h1>
          </div>
          <div className="flex items-center gap-3 bg-slate-50 border border-slate-200 rounded-lg px-4 py-3">
            <span className="text-3xl font-bold font-mono text-slate-900">{currentScore.toFixed(1)}</span>
            <Badge variant={riskDetails.variant}>{riskDetails.label}</Badge>
          </div>
        </div>
      </div>

      <Card>
        <div className="flex items-center justify-between border-b border-slate-200 pb-4 mb-4">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-teal-600" />
            <h3 className="text-sm font-semibold text-slate-900">Compliance Trend</h3>
          </div>
        </div>
        {score_history.length < 2 ? (
          <div className="h-48 flex items-center justify-center text-slate-500 text-sm">
            At least 2 audits required for trend chart. Current: {score_history.length}
          </div>
        ) : (
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={score_history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} vertical={false} />
                <XAxis dataKey="date" stroke={CHART_AXIS} fontSize={10} tickLine={false} axisLine={false} />
                <YAxis stroke={CHART_AXIS} fontSize={10} domain={[0, 100]} tickLine={false} axisLine={false} />
                <Tooltip content={<ScoreTooltip />} />
                <ReferenceLine y={80} stroke="#10b981" strokeDasharray="3 3" strokeOpacity={0.4} />
                <ReferenceLine y={50} stroke="#f43f5e" strokeDasharray="3 3" strokeOpacity={0.4} />
                <Line type="monotone" dataKey="score" stroke={CHART_COLORS.primary} strokeWidth={2} dot={{ r: 4, fill: CHART_COLORS.primary }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </Card>

      <div className="card overflow-hidden p-0">
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Award className="h-5 w-5 text-teal-600" />
            <h3 className="text-sm font-semibold text-slate-900">Audit History</h3>
          </div>
          <Badge variant="default">{history.length} runs</Badge>
        </div>
        <Table>
          <TableHead>
            <tr>
              <TableCell header>Date</TableCell>
              <TableCell header>Audit ID</TableCell>
              <TableCell header className="text-center">Score</TableCell>
              <TableCell header className="text-right">Leakage</TableCell>
              <TableCell header className="text-center">Discrepancies</TableCell>
              <TableCell header className="text-center">Report</TableCell>
            </tr>
          </TableHead>
          <TableBody>
            {history.map((audit) => {
              const auditRisk = getRiskDetails(audit.score);
              return (
                <TableRow key={audit.audit_id} onClick={() => onSelectAudit(audit.audit_id, 'COMPLETE')}>
                  <TableCell>
                    <span className="flex items-center gap-2 text-xs">
                      <Calendar className="h-3.5 w-3.5 text-slate-400" />
                      {new Date(audit.created_at).toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' })}
                    </span>
                  </TableCell>
                  <TableCell className="font-mono text-xs text-teal-600">{audit.audit_id}</TableCell>
                  <TableCell className="text-center">
                    <span className="font-mono font-semibold">{audit.score.toFixed(1)}</span>
                    <Badge variant={auditRisk.variant} className="ml-2">{auditRisk.label.split(' ')[0]}</Badge>
                  </TableCell>
                  <TableCell className="text-right font-mono font-semibold text-rose-600">
                    ${parseFloat(audit.total_leakage).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </TableCell>
                  <TableCell className="text-center">
                    <Badge variant={audit.discrepancy_count > 0 ? 'critical' : 'success'}>{audit.discrepancy_count}</Badge>
                  </TableCell>
                  <TableCell className="text-center">
                    <button type="button" onClick={(e) => { e.stopPropagation(); onSelectAudit(audit.audit_id, 'COMPLETE'); }} className="inline-flex items-center gap-1 text-xs font-semibold text-teal-600 hover:text-teal-800">
                      <FileText className="h-3.5 w-3.5" /> Open
                    </button>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>

      {history.length >= 2 && (
        <div className="mt-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                Negotiation Intelligence
              </h2>
              <p className="text-sm text-slate-500">Based on {history.length} audits covering your entire history.</p>
            </div>
            <Button onClick={handleGenerateBrief} disabled={briefLoading} size="lg">
              {briefLoading ? <><RefreshCw className="h-4 w-4 mr-2 animate-spin" /> Analysing {history.length} audits...</> : 'Generate Negotiation Brief'}
            </Button>
          </div>
          {activeBrief && (
            <div className="mt-4">
              <NegotiationBriefCard brief={activeBrief} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ScoreTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const item = payload[0].payload;
  return (
    <div className="bg-white border border-slate-200 rounded-lg shadow-card px-3 py-2 text-xs">
      <p className="text-slate-500 font-semibold uppercase">Date</p>
      <p className="text-slate-900 font-mono">{item.date}</p>
      <p className="text-slate-500 font-semibold uppercase mt-2">Score</p>
      <p className="text-teal-600 font-bold font-mono">{item.score.toFixed(1)}%</p>
    </div>
  );
}
