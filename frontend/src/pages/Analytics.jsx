/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Visualizes leakage data, supplier score charts, and billing audits.
 * 
 * What it means:
 * Analytics dashboard overview page.
 * 
 * Importance in Project:
 * High. The flagship screen summarizing financial recovery metrics.
 */

import { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
  PieChart,
  Pie,
  Cell,
  Line,
  Area
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  RefreshCw,
  Building2,
  Calendar,
  DollarSign,
  Layers,
  FileSpreadsheet,
  Clock,
  ShieldAlert,
  Percent,
  Scale,
  AlertCircle,
  Sparkles
} from 'lucide-react';
import { getAnalytics, getHeatmap } from '../api';
import PageHeader from '../components/layout/PageHeader';
import StatCard from '../components/ui/StatCard';
import Button from '../components/ui/Button';
import Badge, { severityVariant } from '../components/ui/Badge';
import Tabs from '../components/ui/Tabs';
import Spinner from '../components/ui/Spinner';
import Card from '../components/ui/Card';
import {
  CHART_GRID,
  CHART_AXIS,
  CHART_COLORS,
  formatDollar,
  getHeatmapCellClass,
} from '../utils/chartTheme';

const PERIOD_TABS = [
  { id: '30d', label: '30 Days' },
  { id: '90d', label: '90 Days' },
  { id: '1y', label: '1 Year' },
  { id: 'all', label: 'All Time' },
];

// Display names mapping for discrepancy/clause types
const CLAUSE_DISPLAY_NAMES = {
  overcharge: "Overcharge",
  missed_discount: "Missed Discount",
  unapplied_penalty: "SLA / Penalty",
  incorrect_rate: "Wrong Rate",
  missing_credit: "Missing Credit",
  period_mismatch: "Period Error"
};

// Map clause type to icons
const CLAUSE_ICONS = {
  overcharge: ShieldAlert,
  missed_discount: Percent,
  unapplied_penalty: Scale,
  incorrect_rate: FileSpreadsheet,
  missing_credit: Layers,
  period_mismatch: Clock
};

const TOOLTIP_CLASS = 'bg-white border border-slate-200 rounded-lg shadow-card p-3 text-xs';
const PIE_COLORS = [
  CHART_COLORS.primary,
  '#a855f7',
  CHART_COLORS.rose,
  '#ec4899',
  CHART_COLORS.amber,
  CHART_COLORS.emerald,
];

// Custom Tooltips declared outside of the main component render context
const MonthTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    return (
      <div className={TOOLTIP_CLASS}>
        <p className="text-[10px] text-slate-500 font-semibold uppercase tracking-wide">Month</p>
        <p className="text-slate-900 text-xs font-bold font-mono mt-0.5">{payload[0].payload.month}</p>
        <p className="text-[10px] text-slate-500 font-semibold uppercase tracking-wide mt-2">Identified Leakage</p>
        <p className="text-rose-600 text-sm font-bold font-mono mt-0.5">{formatDollar(payload[0].payload.total_leakage)}</p>
        <p className="text-[10px] text-slate-500 font-semibold uppercase tracking-wide mt-2">Audits Conducted</p>
        <p className="text-teal-600 text-sm font-bold font-mono mt-0.5">{payload[0].payload.audit_count}</p>
      </div>
    );
  }
  return null;
};

const SupplierTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const item = payload[0].payload;
    return (
      <div className={TOOLTIP_CLASS}>
        <p className="text-[10px] text-slate-500 font-semibold uppercase tracking-wide">Supplier</p>
        <p className="text-slate-900 text-xs font-bold mt-0.5">{item.supplier_name}</p>
        <p className="text-[10px] text-slate-500 font-semibold uppercase tracking-wide mt-2">Total Leakage</p>
        <p className="text-rose-600 text-sm font-bold font-mono mt-0.5">{formatDollar(item.total_leakage)}</p>
        <p className="text-[10px] text-slate-500 font-semibold uppercase tracking-wide mt-2">Audits Run</p>
        <p className="text-teal-600 text-sm font-bold font-mono mt-0.5">{item.audit_count}</p>
      </div>
    );
  }
  return null;
};

const TypeTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const item = payload[0].payload;
    return (
      <div className={TOOLTIP_CLASS}>
        <p className="text-[10px] text-slate-500 font-semibold uppercase tracking-wide">Discrepancy Type</p>
        <p className="text-slate-900 text-xs font-bold mt-0.5 capitalize">{item.discrepancy_type.replace('_', ' ')}</p>
        <p className="text-[10px] text-slate-500 font-semibold uppercase tracking-wide mt-2">Total Leakage</p>
        <p className="text-rose-600 text-sm font-bold font-mono mt-0.5">{formatDollar(item.total_leakage)}</p>
        <p className="text-[10px] text-slate-500 font-semibold uppercase tracking-wide mt-2">Discrepancy Count</p>
        <p className="text-teal-600 text-sm font-bold font-mono mt-0.5">{item.count}</p>
      </div>
    );
  }
  return null;
};

export default function Analytics() {
  const [period, setPeriod] = useState('30d');
  const [data, setData] = useState(null);
  const [heatmapData, setHeatmapData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    const loadAnalytics = async () => {
      setLoading(true);
      setError(null);
      try {
        const [overviewRes, heatmapRes] = await Promise.all([
          getAnalytics(period),
          getHeatmap(period)
        ]);
        setData(overviewRes);
        setHeatmapData(heatmapRes);
      } catch (err) {
        console.error("Error loading analytics:", err);
        setError("Failed to load analytics dashboard data. Please try again.");
      } finally {
        setLoading(false);
      }
    };
    loadAnalytics();
  }, [period, reload]);

  if (loading) {
    return (
      <div className="py-24">
        <Spinner label="Computing leakage trend analytics..." />
      </div>
    );
  }

  if (error || !data || !heatmapData) {
    return (
      <div className="flex flex-col items-center justify-center py-16 space-y-4 max-w-md mx-auto text-center">
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl">
          <AlertTriangle className="h-8 w-8 text-rose-600" />
        </div>
        <h3 className="text-lg font-bold text-slate-900">Error Loading Analytics</h3>
        <p className="text-slate-600 text-sm">{error || "No data available."}</p>
        <Button size="sm" onClick={() => setReload(prev => prev + 1)}>
          <RefreshCw className="h-3.5 w-3.5" />
          Try Again
        </Button>
      </div>
    );
  }

  const { period_label, kpis, leakage_by_month, leakage_by_supplier, leakage_by_type, severity_breakdown, top_findings } = data;

  // Helper to color supplier bars
  const getSupplierBarColor = (leakage) => {
    if (leakage >= 50000) return '#ef4444'; // Red (High risk)
    if (leakage >= 15000) return '#f59e0b'; // Amber (Medium risk)
    return '#10b981'; // Green (Low risk)
  };

  // Transform severity breakdown to recharts array
  const severityChartData = [
    { name: 'CRITICAL', count: severity_breakdown.CRITICAL.count, leakage: parseFloat(severity_breakdown.CRITICAL.total_leakage) },
    { name: 'HIGH', count: severity_breakdown.HIGH.count, leakage: parseFloat(severity_breakdown.HIGH.total_leakage) },
    { name: 'MEDIUM', count: severity_breakdown.MEDIUM.count, leakage: parseFloat(severity_breakdown.MEDIUM.total_leakage) }
  ];

  const trendValue = period === 'all'
    ? 'N/A'
    : `${kpis.leakage_trend_pct > 0 ? '↑' : '↓'} ${Math.abs(kpis.leakage_trend_pct).toFixed(1)}%`;

  const trendSubtext = period === 'all'
    ? 'No comparison baseline'
    : kpis.leakage_trend_pct > 0
      ? 'worse than prev period'
      : 'better than prev period';

  return (
    <div className="space-y-6">

      <PageHeader
        title="Leakage Trend Analytics"
        description="Aggregate leakage metrics, supplier risk concentrations, severity breakdowns, and contract anomalies."
        actions={
          <Tabs tabs={PERIOD_TABS} activeTab={period} onChange={setPeriod} />
        }
      />

      {/* SECTION 2 — KPI Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          label="Total Leakage"
          value={formatDollar(kpis.total_leakage_identified)}
          subtext="Identified billing loss"
          icon={DollarSign}
          iconColor="text-rose-600"
          iconBg="bg-rose-50"
        />
        <StatCard
          label="Audits Conducted"
          value={kpis.total_audits_run}
          subtext="Completed audit runs"
          icon={Layers}
        />
        <StatCard
          label="Avg Loss / Run"
          value={formatDollar(kpis.avg_leakage_per_audit)}
          subtext="Average leak per audit"
          icon={DollarSign}
        />
        <StatCard
          label="Suppliers Audited"
          value={kpis.total_suppliers_audited}
          subtext="Audited vendor entities"
          icon={Building2}
        />
        <StatCard
          label="Leakage Trend"
          value={trendValue}
          subtext={trendSubtext}
          icon={kpis.leakage_trend_pct > 0 ? TrendingUp : TrendingDown}
          iconColor={kpis.leakage_trend_pct > 0 ? 'text-rose-600' : 'text-emerald-600'}
          iconBg={kpis.leakage_trend_pct > 0 ? 'bg-rose-50' : 'bg-emerald-50'}
        />
      </div>

      {/* SECTION 3 — Two charts side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Left Chart: Leakage Over Time */}
        <Card>
          <div className="flex items-center justify-between border-b border-slate-200 pb-4 mb-4">
            <div className="flex items-center gap-2.5">
              <Calendar className="h-5 w-5 text-teal-600" />
              <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider">Leakage Over Time</h3>
            </div>
            <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">
              {period_label} Monthly Summary
            </span>
          </div>

          <div className="relative h-80 w-full">
            {leakage_by_month.length === 0 ? (
              <div className="h-full flex items-center justify-center text-slate-500 text-xs font-medium italic">
                No monthly historical leakage data available.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={leakage_by_month} margin={{ top: 10, right: -5, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorLeakage" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={CHART_COLORS.rose} stopOpacity={0.15}/>
                      <stop offset="95%" stopColor={CHART_COLORS.rose} stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} vertical={false} />
                  <XAxis
                    dataKey="month"
                    stroke={CHART_AXIS}
                    fontSize={10}
                    fontWeight="bold"
                    tickLine={false}
                    dy={10}
                  />
                  <YAxis
                    yAxisId="left"
                    stroke={CHART_COLORS.rose}
                    fontSize={10}
                    fontWeight="bold"
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(v) => `$${Math.round(v/1000)}k`}
                  />
                  <YAxis
                    yAxisId="right"
                    orientation="right"
                    stroke={CHART_COLORS.primary}
                    fontSize={10}
                    fontWeight="bold"
                    tickLine={false}
                    axisLine={false}
                  />
                  <Tooltip content={<MonthTooltip />} cursor={{ stroke: CHART_GRID, strokeWidth: 1 }} />
                  <Legend
                    verticalAlign="top"
                    height={36}
                    iconType="circle"
                    iconSize={8}
                    wrapperStyle={{ fontSize: '10px', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '0.05em', color: CHART_AXIS }}
                  />
                  <Area
                    yAxisId="left"
                    type="monotone"
                    dataKey="total_leakage"
                    stroke="none"
                    fill="url(#colorLeakage)"
                  />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="total_leakage"
                    name="Leakage ($)"
                    stroke={CHART_COLORS.rose}
                    strokeWidth={3}
                    dot={{ r: 4, stroke: CHART_COLORS.rose, strokeWidth: 2, fill: '#ffffff' }}
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="audit_count"
                    name="Audit Runs"
                    stroke={CHART_COLORS.primary}
                    strokeWidth={2}
                    strokeDasharray="4 4"
                    dot={{ r: 3, stroke: CHART_COLORS.primary, strokeWidth: 1.5, fill: '#ffffff' }}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            )}
          </div>
        </Card>

        {/* Right Chart: Leakage by Supplier */}
        <Card>
          <div className="flex items-center justify-between border-b border-slate-200 pb-4 mb-4">
            <div className="flex items-center gap-2.5">
              <Building2 className="h-5 w-5 text-teal-600" />
              <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider">Top Suppliers by Leakage</h3>
            </div>
            <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">
              Top 10 Risk Concentrations
            </span>
          </div>

          <div className="relative h-80 w-full">
            {leakage_by_supplier.length === 0 ? (
              <div className="h-full flex items-center justify-center text-slate-500 text-xs font-medium italic">
                No supplier risk leakage data available.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  layout="vertical"
                  data={leakage_by_supplier}
                  margin={{ top: 10, right: 10, left: 10, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} horizontal={false} />
                  <XAxis
                    type="number"
                    stroke={CHART_AXIS}
                    fontSize={10}
                    fontWeight="bold"
                    tickLine={false}
                    tickFormatter={(v) => `$${Math.round(v/1000)}k`}
                  />
                  <YAxis
                    type="category"
                    dataKey="supplier_name"
                    stroke={CHART_AXIS}
                    fontSize={10}
                    fontWeight="bold"
                    tickLine={false}
                    width={90}
                  />
                  <Tooltip content={<SupplierTooltip />} cursor={{ fill: '#f1f5f9' }} />
                  <Bar dataKey="total_leakage" radius={[0, 4, 4, 0]}>
                    {leakage_by_supplier.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={getSupplierBarColor(parseFloat(entry.total_leakage))} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </Card>

      </div>

      {/* SECTION 4 — Two more charts side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Left Chart: Leakage by Discrepancy Type */}
        <Card>
          <div className="flex items-center justify-between border-b border-slate-200 pb-4 mb-4">
            <div className="flex items-center gap-2.5">
              <Layers className="h-5 w-5 text-teal-600" />
              <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider">Leakage by Discrepancy Type</h3>
            </div>
            <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">
              Anomalies Categorization
            </span>
          </div>

          <div className="h-80 w-full flex flex-col sm:flex-row items-center justify-center gap-6">
            {leakage_by_type.length === 0 ? (
              <div className="h-full flex items-center justify-center text-slate-500 text-xs font-medium italic">
                No discrepancy categorization data available.
              </div>
            ) : (
              <>
                {/* Donut Chart */}
                <div className="relative h-60 w-60 flex-shrink-0">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={leakage_by_type}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={80}
                        paddingAngle={3}
                        dataKey="total_leakage"
                      >
                        {leakage_by_type.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip content={<TypeTooltip />} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                {/* Custom Legend Ledger */}
                <div className="flex-1 space-y-2.5 overflow-y-auto max-h-64 pr-2 w-full">
                  {leakage_by_type.map((entry, index) => (
                    <div
                      key={entry.discrepancy_type}
                      className="flex items-center justify-between text-xs p-2 rounded-lg bg-slate-50 border border-slate-200"
                    >
                      <div className="flex items-center space-x-2 truncate pr-2">
                        <div className="h-2.5 w-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: PIE_COLORS[index % PIE_COLORS.length] }} />
                        <span className="text-slate-700 font-semibold capitalize truncate">
                          {entry.discrepancy_type.replace(/_/g, ' ')}
                        </span>
                      </div>
                      <div className="flex items-baseline space-x-2 flex-shrink-0 text-right">
                        <span className="font-mono font-semibold text-slate-900">{formatDollar(entry.total_leakage)}</span>
                        <span className="text-[10px] text-slate-500 font-semibold">({entry.count})</span>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </Card>

        {/* Right Chart: Severity Breakdown */}
        <Card>
          <div className="flex items-center justify-between border-b border-slate-200 pb-4 mb-4">
            <div className="flex items-center gap-2.5">
              <AlertTriangle className="h-5 w-5 text-teal-600" />
              <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider">Severity Risk Breakdown</h3>
            </div>
            <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">
              Critical, High & Medium Aggregation
            </span>
          </div>

          <div className="relative h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={severityChartData}
                margin={{ top: 10, right: -5, left: -20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} vertical={false} />
                <XAxis
                  dataKey="name"
                  stroke={CHART_AXIS}
                  fontSize={10}
                  fontWeight="bold"
                  tickLine={false}
                />
                <YAxis
                  yAxisId="left"
                  stroke={CHART_COLORS.primary}
                  fontSize={10}
                  fontWeight="bold"
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(v) => `$${Math.round(v/1000)}k`}
                />
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  stroke={CHART_COLORS.emerald}
                  fontSize={10}
                  fontWeight="bold"
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip
                  cursor={{ fill: '#f1f5f9' }}
                  formatter={(value, name) => name === 'leakage' ? formatDollar(value) : `${value} findings`}
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}
                  labelStyle={{ color: '#0f172a', fontWeight: 'bold' }}
                  itemStyle={{ color: '#475569' }}
                />
                <Legend
                  verticalAlign="top"
                  height={36}
                  iconType="square"
                  iconSize={8}
                  wrapperStyle={{ fontSize: '10px', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '0.05em', color: CHART_AXIS }}
                />
                <Bar
                  yAxisId="left"
                  dataKey="leakage"
                  name="Leakage ($)"
                  radius={[4, 4, 0, 0]}
                  barSize={24}
                >
                  <Cell fill="#ef4444" /> {/* CRITICAL */}
                  <Cell fill="#f97316" /> {/* HIGH */}
                  <Cell fill="#eab308" /> {/* MEDIUM */}
                </Bar>
                <Bar
                  yAxisId="right"
                  dataKey="count"
                  name="Finding Count"
                  fill={CHART_COLORS.emerald}
                  radius={[4, 4, 0, 0]}
                  barSize={12}
                  opacity={0.8}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

      </div>

      {/* SECTION 5 — Top 5 Largest Findings Table */}
      <div className="card overflow-hidden p-0">
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <FileSpreadsheet className="h-5 w-5 text-teal-600" />
            <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider">Top 5 Largest Discrepancy Findings</h3>
          </div>
          <Badge variant="default">Ranked by Dollar Delta</Badge>
        </div>

        <div className="overflow-x-auto">
          {top_findings.length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-sm font-medium">
              No discrepancy findings recorded in this period.
            </div>
          ) : (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 text-[10px] uppercase font-semibold text-slate-500 bg-slate-50">
                  <th className="py-4 px-6">Supplier</th>
                  <th className="py-4 px-6">Discrepancy Type</th>
                  <th className="py-4 px-6 text-center">Severity</th>
                  <th className="py-4 px-6 text-right">Identified Leakage</th>
                  <th className="py-4 px-6">Clause Reference</th>
                  <th className="py-4 px-6">Audit Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {top_findings.map((finding, idx) => (
                  <tr key={`finding-${idx}`} className="hover:bg-slate-50 transition-colors">
                    <td className="py-4 px-6 font-semibold text-slate-900 text-sm">
                      {finding.supplier_name}
                    </td>
                    <td className="py-4 px-6 text-xs text-slate-600 capitalize">
                      {finding.discrepancy_type.replace(/_/g, ' ')}
                    </td>
                    <td className="py-4 px-6 text-center">
                      <Badge variant={severityVariant(finding.severity)}>
                        {finding.severity}
                      </Badge>
                    </td>
                    <td className="py-4 px-6 text-right font-mono font-semibold text-rose-600 text-sm">
                      ${parseFloat(finding.delta).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-4 px-6 text-slate-500 text-xs font-medium max-w-xs truncate" title={finding.clause_reference}>
                      {finding.clause_reference}
                    </td>
                    <td className="py-4 px-6 text-slate-500 text-xs font-mono">
                      {finding.audit_date}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* SECTION 6 — Clause Violation Heatmap */}
      <div className="card overflow-hidden p-0">
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Layers className="h-5 w-5 text-teal-600" />
            <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider">Clause Violation Heatmap</h3>
          </div>
          <Badge variant="default">Violations Frequency & Intensity</Badge>
        </div>

        <div className="p-6 bg-slate-50">
          {heatmapData.suppliers.length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-sm font-medium">
              No clause violation data recorded in this period.
            </div>
          ) : (
            <div className="space-y-6">
              <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
                <table className="w-full text-left border-collapse min-w-[900px]">
                  <thead>
                    <tr className="border-b border-slate-200 text-[10px] uppercase font-semibold text-slate-500 bg-slate-50">
                      <th className="py-4 px-6 select-none">Supplier</th>
                      {heatmapData.clause_types.map(c => (
                        <th key={c} className="py-4 px-4 text-center select-none w-36">
                          {CLAUSE_DISPLAY_NAMES[c] || c}
                        </th>
                      ))}
                      <th className="py-4 px-6 text-right select-none w-40">Supplier Total</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {(() => {
                      let maxCount = 0;
                      heatmapData.suppliers.forEach(s => {
                        heatmapData.clause_types.forEach(c => {
                          const count = heatmapData.grid[s]?.[c]?.count || 0;
                          if (count > maxCount) {
                            maxCount = count;
                          }
                        });
                      });

                      return heatmapData.suppliers.map(supplier => {
                        const rowTotal = heatmapData.row_totals[supplier] || { count: 0, total_leakage: 0 };
                        return (
                          <tr key={supplier} className="hover:bg-slate-50 transition-colors">
                            <td className="py-4 px-6 font-semibold text-slate-900 text-sm whitespace-nowrap">
                              {supplier}
                            </td>

                            {heatmapData.clause_types.map(c => {
                              const cell = heatmapData.grid[supplier]?.[c] || { count: 0, total_leakage: 0 };
                              const count = cell.count || 0;
                              const leakage = cell.total_leakage || 0;
                              const cellClass = getHeatmapCellClass(count, maxCount);
                              const tooltip = `${supplier} | ${CLAUSE_DISPLAY_NAMES[c] || c} | ${count} violations | ${formatDollar(leakage)} leakage`;

                              return (
                                <td
                                  key={c}
                                  className={`py-3 px-4 text-center cursor-help font-mono ${cellClass}`}
                                  title={tooltip}
                                >
                                  <div className="text-base font-bold tracking-tight">{count}</div>
                                  <div className="text-[9px] opacity-75 mt-0.5">{formatDollar(leakage)}</div>
                                </td>
                              );
                            })}

                            <td className="py-4 px-6 text-right font-mono bg-slate-50 border-l border-slate-200">
                              <div className="text-sm font-semibold text-slate-700">{rowTotal.count}</div>
                              <div className="text-[10px] text-rose-600 font-semibold mt-0.5">{formatDollar(rowTotal.total_leakage)}</div>
                            </td>
                          </tr>
                        );
                      });
                    })()}

                    <tr className="border-t-2 border-slate-200 bg-slate-50 font-mono">
                      <td className="py-4 px-6 font-semibold text-slate-500 text-xs uppercase select-none">
                        Total
                      </td>
                      {heatmapData.clause_types.map(c => {
                        const colTotal = heatmapData.column_totals[c] || { count: 0, total_leakage: 0 };
                        return (
                          <td key={c} className="py-4 px-4 text-center border-l border-slate-200">
                            <div className="text-sm font-bold text-slate-700">{colTotal.count}</div>
                            <div className="text-[10px] text-rose-600 font-semibold mt-0.5">{formatDollar(colTotal.total_leakage)}</div>
                          </td>
                        );
                      })}
                      <td className="py-4 px-6 text-right bg-slate-100 border-l border-slate-200">
                        {(() => {
                          const grandTotalCount = Object.values(heatmapData.column_totals).reduce((sum, c) => sum + (c.count || 0), 0);
                          const grandTotalLeakage = Object.values(heatmapData.column_totals).reduce((sum, c) => sum + parseFloat(c.total_leakage || 0), 0);
                          return (
                            <>
                              <div className="text-sm font-bold text-slate-900">{grandTotalCount}</div>
                              <div className="text-xs text-rose-600 font-bold mt-0.5">{formatDollar(grandTotalLeakage)}</div>
                            </>
                          );
                        })()}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* SECTION 7 — Clause Insight Cards & Supplier Vulnerability Profiles */}
      {heatmapData.suppliers.length > 0 && (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <div className="xl:col-span-2 space-y-4">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-teal-600" />
              <h4 className="text-xs font-semibold text-slate-900 uppercase tracking-wider">Clause-Specific Procurement Recommendations</h4>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {(() => {
                const activeInsights = [...heatmapData.insights.clause_insights]
                  .filter(ci => ci.total_count > 0)
                  .sort((a, b) => parseFloat(b.total_leakage) - parseFloat(a.total_leakage));

                const maxViolationCount = Math.max(...activeInsights.map(ci => ci.total_count), 0);

                return activeInsights.map((ci, idx) => {
                  const ySuppliers = Object.values(heatmapData.grid).filter(
                    sGrid => (sGrid[ci.clause_type]?.count || 0) > 0
                  ).length;
                  const IconComponent = CLAUSE_ICONS[ci.clause_type] || AlertCircle;
                  const isMostViolated = ci.total_count === maxViolationCount && ci.total_count > 0;

                  const borderStyle = isMostViolated
                    ? "border-l-4 border-rose-500"
                    : idx === 1
                      ? "border-l-4 border-amber-500"
                      : "border-l-4 border-teal-500";

                  const yAudits = Object.keys(heatmapData.grid)
                    .filter(s => (heatmapData.grid[s]?.[ci.clause_type]?.count || 0) > 0)
                    .reduce((sum, s) => {
                      const sData = data.leakage_by_supplier?.find(lbs => lbs.supplier_name === s);
                      return sum + (sData?.audit_count || 0);
                    }, 0) || ci.total_count;

                  return (
                    <div key={ci.clause_type} className={`card p-5 space-y-3 ${borderStyle}`}>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2.5">
                          <div className={`p-1.5 rounded-lg ${
                            isMostViolated
                              ? "bg-rose-50 border border-rose-200 text-rose-600"
                              : idx === 1
                                ? "bg-amber-50 border border-amber-200 text-amber-600"
                                : "bg-teal-50 border border-teal-200 text-teal-600"
                          }`}>
                            <IconComponent className="h-4 w-4" />
                          </div>
                          <span className="font-semibold text-slate-900 text-sm">
                            {CLAUSE_DISPLAY_NAMES[ci.clause_type] || ci.clause_type}
                          </span>
                        </div>
                        <Badge variant="default">Rank #{idx + 1}</Badge>
                      </div>

                      <div className="grid grid-cols-2 gap-4 bg-slate-50 p-3 rounded-lg border border-slate-200">
                        <div>
                          <span className="text-[10px] text-slate-500 font-semibold block uppercase tracking-wider">Violations</span>
                          <span className="text-xs font-semibold font-mono text-slate-900">
                            {ci.total_count} <span className="text-[9px] text-slate-500 font-normal">times across</span> {ySuppliers} <span className="text-[9px] text-slate-500 font-normal">vendor{ySuppliers !== 1 ? 's' : ''}</span>
                          </span>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-500 font-semibold block uppercase tracking-wider">Total Leakage</span>
                          <span className="text-xs font-semibold font-mono text-rose-600">
                            {formatDollar(ci.total_leakage)}
                          </span>
                        </div>
                      </div>

                      <div className="space-y-1.5 border-t border-slate-200 pt-2.5">
                        <p className="text-xs text-slate-600 leading-normal italic">
                          {CLAUSE_DISPLAY_NAMES[ci.clause_type] || ci.clause_type} violations have caused <span className="font-semibold text-slate-900">{formatDollar(ci.total_leakage)}</span> in leakage across {yAudits} audits.
                        </p>
                        <p className="text-xs text-slate-700 leading-relaxed font-medium">
                          {ci.recommendation}
                        </p>
                      </div>
                    </div>
                  );
                });
              })()}
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Building2 className="h-4 w-4 text-teal-600" />
              <h4 className="text-xs font-semibold text-slate-900 uppercase tracking-wider">Supplier Insight Rows</h4>
            </div>

            <div className="space-y-3">
              {heatmapData.suppliers.map(supplier => {
                const rowTotal = heatmapData.row_totals[supplier] || { count: 0, total_leakage: 0 };

                const getMostViolatedClauseForSupplier = (s) => {
                  const sGrid = heatmapData.grid[s];
                  if (!sGrid) return "None";
                  let maxVal = -1;
                  let mostViolated = "None";
                  Object.keys(sGrid).forEach(c => {
                    if (sGrid[c].count > maxVal) {
                      maxVal = sGrid[c].count;
                      mostViolated = CLAUSE_DISPLAY_NAMES[c] || c;
                    }
                  });
                  return maxVal > 0 ? mostViolated : "None";
                };

                const mostViolated = getMostViolatedClauseForSupplier(supplier);

                return (
                  <div key={supplier} className="card p-4 flex items-center justify-between">
                    <div className="space-y-1 truncate pr-2">
                      <span className="font-semibold text-slate-900 text-sm block truncate">{supplier}</span>
                      <span className="text-[10px] text-slate-500 block uppercase font-semibold tracking-wider">Most Violated Clause</span>
                      {mostViolated === "None" ? (
                        <Badge variant="default">{mostViolated}</Badge>
                      ) : (
                        <Badge variant="critical">{mostViolated}</Badge>
                      )}
                    </div>
                    <div className="text-right flex-shrink-0">
                      <span className="text-[10px] text-slate-500 block uppercase font-semibold tracking-wider font-mono">Row Total</span>
                      <span className="text-sm font-bold font-mono text-rose-600 block">{formatDollar(rowTotal.total_leakage)}</span>
                      <span className="text-[10px] text-slate-500 block font-mono">{rowTotal.count} violation{rowTotal.count !== 1 ? 's' : ''}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
