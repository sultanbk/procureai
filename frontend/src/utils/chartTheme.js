/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Sets standard Recharts colors.
 * 
 * What it means:
 * Dashboard chart style configuration.
 * 
 * Importance in Project:
 * Low. Customizes chart colors for cohesive styling.
 */

export const CHART_COLORS = {
  primary: '#E0292A',
  emerald: '#10b981',
  amber: '#f59e0b',
  rose: '#f43f5e',
  sky: '#0ea5e9',
  slate: '#64748b',
};

export const CHART_GRID = '#e2e8f0';
export const CHART_AXIS = '#64748b';

export const CHART_SERIES = [
  CHART_COLORS.primary,
  CHART_COLORS.emerald,
  CHART_COLORS.amber,
  CHART_COLORS.rose,
  CHART_COLORS.sky,
];

export function getHeatmapCellClass(count, maxCount) {
  if (count === 0) return 'bg-slate-50 text-slate-400 border border-slate-200';
  const intensity = maxCount > 0 ? count / maxCount : 0;
  if (intensity < 0.25) return 'bg-rose-50 text-rose-700 border border-rose-200';
  if (intensity < 0.5) return 'bg-rose-100 text-rose-800 border border-rose-300';
  if (intensity < 0.75) return 'bg-rose-300 text-rose-900 border border-rose-400';
  return 'bg-rose-600 text-white border border-rose-700';
}

export const formatDollar = (value) =>
  `$${Math.round(parseFloat(value) || 0).toLocaleString('en-US')}`;
