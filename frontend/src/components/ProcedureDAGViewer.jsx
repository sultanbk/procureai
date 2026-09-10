/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Renders corporate Standard Operating Procedures (SOPs) as Directed Acyclic Graphs (DAGs)
 * retrieved from SynaptAI Context Substrate (Milvus PS).
 * 
 * What it means:
 * Procedural execution playbook. Converts raw discrepancy findings into step-by-step
 * enterprise recovery workflows governed by corporate policy.
 * 
 * Importance in Project:
 * High. Bridges the gap between identifying overcharges and executing enterprise dispute recovery.
 */

import React, { useState } from 'react';
import {
  GitBranch,
  CheckCircle2,
  Clock,
  Circle,
  ArrowRight,
  Shield,
  UserCheck,
  FileText,
  AlertCircle,
} from 'lucide-react';

export default function ProcedureDAGViewer({ procedureDag, onStepStatusChange }) {
  const [steps, setSteps] = useState(procedureDag?.steps || []);

  if (!procedureDag) {
    return (
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-6 text-center text-slate-500">
        <GitBranch className="w-8 h-8 text-slate-300 mx-auto mb-2" />
        <p className="text-xs font-semibold text-slate-700">No Corporate SOP Attached</p>
        <p className="text-[11px] text-slate-400 mt-1">
          This query does not trigger a governed operational recovery procedure.
        </p>
      </div>
    );
  }

  const toggleStep = (stepId) => {
    const updated = steps.map((step) => {
      if (step.step_id === stepId) {
        const nextStatus =
          step.status === 'COMPLETED'
            ? 'IN_PROGRESS'
            : step.status === 'IN_PROGRESS'
            ? 'PENDING'
            : 'COMPLETED';
        return { ...step, status: nextStatus };
      }
      return step;
    });
    setSteps(updated);
    if (onStepStatusChange) onStepStatusChange(updated);
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm space-y-4 p-5">
      {/* SOP Header */}
      <div className="flex items-start justify-between border-b border-slate-100 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1 bg-pink-50 text-pink-600 rounded border border-pink-100">
              <GitBranch className="w-4 h-4" />
            </span>
            <h4 className="font-bold text-slate-900 text-sm">{procedureDag.name}</h4>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-semibold">
              v{procedureDag.version}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1 leading-relaxed">
            {procedureDag.intent}
          </p>
        </div>

        <div className="text-right shrink-0">
          <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
            SOP Schema
          </span>
          <p className="text-xs font-mono font-bold text-indigo-600 mt-0.5">
            Milvus PS (DAG)
          </p>
        </div>
      </div>

      {/* DAG Workflow Steps Timeline */}
      <div className="space-y-3 relative">
        {/* Subtle connecting vertical line */}
        <div className="absolute left-[19px] top-4 bottom-4 w-0.5 bg-slate-200 -z-0" />

        {steps.map((step, idx) => {
          const isCompleted = step.status === 'COMPLETED';
          const isInProgress = step.status === 'IN_PROGRESS';

          return (
            <div
              key={step.step_id}
              className={`relative z-10 flex items-start gap-3.5 p-3 rounded-lg border transition-all cursor-pointer ${
                isCompleted
                  ? 'bg-emerald-50/40 border-emerald-200'
                  : isInProgress
                  ? 'bg-indigo-50/40 border-indigo-200 shadow-sm'
                  : 'bg-slate-50/50 border-slate-200 hover:bg-slate-100/50'
              }`}
              onClick={() => toggleStep(step.step_id)}
            >
              {/* Step Status Icon */}
              <div className="shrink-0 mt-0.5">
                {isCompleted ? (
                  <div className="w-8 h-8 rounded-full bg-emerald-500 text-white flex items-center justify-center shadow-sm">
                    <CheckCircle2 className="w-5 h-5" />
                  </div>
                ) : isInProgress ? (
                  <div className="w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center shadow-sm animate-pulse">
                    <Clock className="w-4 h-4" />
                  </div>
                ) : (
                  <div className="w-8 h-8 rounded-full bg-white border-2 border-slate-300 text-slate-400 flex items-center justify-center font-bold text-xs">
                    {idx + 1}
                  </div>
                )}
              </div>

              {/* Step Details */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-bold text-xs text-slate-900 leading-snug">
                    {step.title}
                  </span>
                  <div className="flex items-center gap-2 shrink-0">
                    {step.required_role && (
                      <span className="text-[10px] font-medium bg-slate-100 text-slate-600 px-2 py-0.5 rounded flex items-center gap-1">
                        <UserCheck className="w-3 h-3 text-slate-500" />
                        {step.required_role}
                      </span>
                    )}
                    <span
                      className={`text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${
                        isCompleted
                          ? 'bg-emerald-100 text-emerald-800'
                          : isInProgress
                          ? 'bg-indigo-100 text-indigo-800'
                          : 'bg-slate-200 text-slate-600'
                      }`}
                    >
                      {step.status.replace(/_/g, ' ')}
                    </span>
                  </div>
                </div>

                <p className="text-[11px] text-slate-600 mt-1 leading-relaxed">
                  {step.description}
                </p>

                {idx < steps.length - 1 && (
                  <div className="flex items-center gap-1 text-[10px] text-slate-400 font-mono mt-2">
                    <ArrowRight className="w-3 h-3 text-indigo-400" />
                    <span>Precedes Step {idx + 2}</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer Notice */}
      <div className="bg-slate-50 rounded-lg p-2.5 border border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
        <span className="flex items-center gap-1.5">
          <Shield className="w-3.5 h-3.5 text-indigo-500" />
          Governance: Verified against Enterprise Dispute SOP (Neo4j HAS_STEP edges)
        </span>
        <span className="font-mono text-[10px]">Click any step to toggle completion</span>
      </div>
    </div>
  );
}
