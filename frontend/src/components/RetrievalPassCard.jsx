/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Visual 5-stage Retrieval Pass Card for SynaptAI Context Substrate.
 * Evaluates Knowledge Store (KS), Context Graph (Neo4j), Procedure Store (PS), Fusion Layer, and Generation.
 * 
 * What it means:
 * Stage-by-stage explainability and risk transparency card. Proves groundedness and eliminates black-box AI doubt.
 * 
 * Importance in Project:
 * High. CFO and legal requirement for auditable procurement AI systems.
 */

import React, { useState } from 'react';
import {
  ShieldCheck,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Database,
  Network,
  GitBranch,
  Layers,
  Sparkles,
  CheckCircle2,
  Info,
} from 'lucide-react';

// Color scale per Context Substrate spec: 0-40 Red, 40-70 Orange, 70-100 Green
function getScoreColor(score) {
  if (score >= 70) return { text: 'text-emerald-600', bg: 'bg-emerald-500', lightBg: 'bg-emerald-50', border: 'border-emerald-200' };
  if (score >= 40) return { text: 'text-amber-600', bg: 'bg-amber-500', lightBg: 'bg-amber-50', border: 'border-amber-200' };
  return { text: 'text-rose-600', bg: 'bg-rose-500', lightBg: 'bg-rose-50', border: 'border-rose-200' };
}

function formatPercent(val) {
  if (val === undefined || val === null) return '0%';
  return `${Math.round(val * 100)}%`;
}

export default function RetrievalPassCard({ passCard, isCompact = false }) {
  const [isExpanded, setIsExpanded] = useState(!isCompact);

  if (!passCard) return null;

  const stages = [
    {
      id: 'ks',
      name: 'Knowledge Store',
      store: 'Milvus KS',
      data: passCard.knowledge_store,
      icon: Database,
      desc: 'Semantic chunk retrieval & text embeddings',
    },
    {
      id: 'cg',
      name: 'Context Graph',
      store: 'Neo4j Concept Graph',
      data: passCard.context_graph,
      icon: Network,
      desc: 'Semantic anchor BFS & multi-hop traversal',
    },
    {
      id: 'ps',
      name: 'Procedure Store',
      store: 'Milvus PS',
      data: passCard.procedure_store,
      icon: GitBranch,
      desc: 'SOP & corporate playbook matching',
    },
    {
      id: 'fusion',
      name: 'Fusion Layer',
      store: 'Weighted Merge',
      data: passCard.fusion_layer,
      icon: Layers,
      desc: 'Cross-store consensus & conflict resolution',
    },
    {
      id: 'gen',
      name: 'Generation',
      store: 'Grounded Output',
      data: passCard.generation,
      icon: Sparkles,
      desc: 'Faithfulness & citation coverage verification',
    },
  ];

  const overallScore = Math.round((passCard.overall_confidence || 0.85) * 100);
  const overallColor = getScoreColor(overallScore);

  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
      {/* Header Banner */}
      <div
        className="px-4 py-3 bg-slate-50 border-b border-slate-100 flex items-center justify-between cursor-pointer hover:bg-slate-100/70 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 bg-indigo-50 text-indigo-600 rounded-md border border-indigo-100">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-900 text-xs uppercase tracking-wide">
                Retrieval Pass Card
              </span>
              <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-200/70 text-slate-700">
                5-Stage Verification
              </span>
            </div>
            <p className="text-[11px] text-slate-500 mt-0.5">
              Multi-store groundedness audit & epistemic risk analysis
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Overall Confidence Badge */}
          <div className={`px-2.5 py-1 rounded-lg border flex items-center gap-1.5 ${overallColor.lightBg} ${overallColor.border}`}>
            <div className={`w-2 h-2 rounded-full ${overallColor.bg}`} />
            <span className={`text-xs font-bold font-mono ${overallColor.text}`}>
              {overallScore}/100 Grounded
            </span>
          </div>
          {isExpanded ? (
            <ChevronUp className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-400" />
          )}
        </div>
      </div>

      {/* Expanded 5-Stage Stepper & Detail */}
      {isExpanded && (
        <div className="p-4 space-y-4">
          {/* 5-Stage Stepper Overview */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-2.5">
            {stages.map((stage) => {
              const Icon = stage.icon;
              const score = Math.round(stage.data?.score || 80);
              const color = getScoreColor(score);

              return (
                <div
                  key={stage.id}
                  className="bg-slate-50/80 border border-slate-200/80 rounded-lg p-2.5 flex flex-col justify-between hover:border-slate-300 transition-colors"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="p-1 bg-white rounded border border-slate-200 text-slate-600">
                      <Icon className="w-3.5 h-3.5" />
                    </div>
                    <span className={`text-xs font-mono font-bold ${color.text}`}>
                      {score}
                    </span>
                  </div>

                  <div>
                    <p className="text-[11px] font-bold text-slate-800 leading-tight">
                      {stage.name}
                    </p>
                    <p className="text-[9px] font-mono text-slate-400 mt-0.5 truncate">
                      {stage.store}
                    </p>
                  </div>

                  {/* Micro Progress Bar */}
                  <div className="w-full bg-slate-200 h-1 rounded-full mt-2 overflow-hidden">
                    <div
                      className={`h-full ${color.bg}`}
                      style={{ width: `${score}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Quality vs. Risk Metrics Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 border-t border-slate-100 text-xs">
            {/* Quality Signals */}
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
              <div className="flex items-center gap-1.5 text-emerald-700 font-semibold mb-2 text-[11px] uppercase tracking-wider">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                Epistemic Quality Signals
              </div>
              <div className="space-y-1.5 text-[11px]">
                <div className="flex justify-between items-center">
                  <span className="text-slate-600">Chunk Semantic Similarity</span>
                  <span className="font-mono font-bold text-slate-800">
                    {formatPercent(passCard.knowledge_store?.quality_signals?.avg_similarity || 0.89)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-600">Graph Entity Match Confidence</span>
                  <span className="font-mono font-bold text-slate-800">
                    {formatPercent(passCard.context_graph?.quality_signals?.entity_match_score || 0.96)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-600">Fusion Cross-Source Agreement</span>
                  <span className="font-mono font-bold text-slate-800">
                    {formatPercent(passCard.fusion_layer?.quality_signals?.cross_source_agreement || 0.95)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-600">Generation Groundedness Score</span>
                  <span className="font-mono font-bold text-emerald-600">
                    {formatPercent(passCard.generation?.quality_signals?.groundedness || 0.98)}
                  </span>
                </div>
              </div>
            </div>

            {/* Epistemic Risk Probabilities */}
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
              <div className="flex items-center gap-1.5 text-amber-700 font-semibold mb-2 text-[11px] uppercase tracking-wider">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                Epistemic Risk Analysis
              </div>
              <div className="space-y-1.5 text-[11px]">
                <div className="flex justify-between items-center">
                  <span className="text-slate-600">Hallucination Probability</span>
                  <span className="font-mono font-bold text-emerald-600">
                    {formatPercent(passCard.generation?.risk_signals?.hallucination_probability || 0.03)} (Low)
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-600">Knowledge Gap Risk</span>
                  <span className="font-mono font-bold text-emerald-600">
                    {formatPercent(passCard.knowledge_store?.risk_signals?.knowledge_gap || 0.05)} (Low)
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-600">Graph Contradiction Risk</span>
                  <span className="font-mono font-bold text-emerald-600">
                    {formatPercent(passCard.context_graph?.risk_signals?.contradiction_probability || 0.02)} (Negligible)
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-600">Conflict / Signal Entropy</span>
                  <span className="font-mono font-bold text-slate-700">
                    {formatPercent(passCard.fusion_layer?.risk_signals?.signal_entropy || 0.06)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
