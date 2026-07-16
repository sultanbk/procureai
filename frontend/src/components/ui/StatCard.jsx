/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Micro stat visualizer with color tags.
 * 
 * What it means:
 * Aggregated stats display.
 * 
 * Importance in Project:
 * Medium. Represents specific key metrics on dashboards.
 */

import { Info } from 'lucide-react';
import Tooltip from './Tooltip';

export default function StatCard({ label, value, subtext, tooltip, icon: Icon, iconColor = 'text-teal-600', iconBg = 'bg-teal-50' }) {
  return (
    <div className="card p-5 transition-all duration-300 hover:shadow-md hover:border-slate-300">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-1.5">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{label}</p>
            {tooltip && (
              <Tooltip content={tooltip} position="top">
                <Info className="h-3.5 w-3.5 text-slate-400 hover:text-slate-600 cursor-help transition-colors stroke-[1.5]" />
              </Tooltip>
            )}
          </div>
          <p className="mt-2 text-2xl font-bold text-slate-900 font-display">{value}</p>
          {subtext && (
            <p className="mt-1 text-xs text-slate-500">{subtext}</p>
          )}
        </div>
        {Icon && (
          <div className={`p-2.5 rounded-xl flex items-center justify-center shrink-0 transition-transform duration-300 hover:scale-105 ${iconBg}`}>
            {typeof Icon === 'string' ? (
              <span className={`font-mono text-xs font-bold ${iconColor}`}>{Icon}</span>
            ) : (
              <Icon className={`h-5 w-5 ${iconColor} stroke-[1.5]`} />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
