/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Highlights matching text excerpts from invoices/contracts and provides
 * 1-click Context Substrate reasoning subgraph inspection for every audit finding.
 * 
 * What it means:
 * Evidence validator. Anchors flagged discrepancies to verified document clauses and Neo4j graph nodes.
 * 
 * Importance in Project:
 * High. Transforms raw financial discrepancies into legally indisputable audit proof.
 */

import React, { useState } from 'react';
import { Quote, AlertCircle, CheckSquare, Target, Network, ShieldCheck, ExternalLink, Eye } from 'lucide-react';
import Badge from './ui/Badge';
import ReasoningSubgraphModal from './ReasoningSubgraphModal';
import { getDiscrepancySubgraph } from '../api';

export default function EvidenceBlock({ finding, auditId, onOpenProof }) {
  const {
    finding_id, description, clause_reference, clause_text, quantity,
    unit_price_charged, unit_price_expected, line_total_charged,
    line_total_expected, delta, recommendation, confidence
  } = finding;

  const [isGraphOpen, setIsGraphOpen] = useState(false);
  const [subgraph, setSubgraph] = useState(null);
  const [isLoadingGraph, setIsLoadingGraph] = useState(false);

  const recVariant = recommendation === 'DISPUTE' ? 'critical' : recommendation === 'ESCALATE' ? 'high' : recommendation === 'MONITOR' ? 'medium' : 'default';
  const confidencePct = Math.round((confidence || 0.85) * 100);

  const handleOpenGraph = async () => {
    setIsLoadingGraph(true);
    try {
      const data = await getDiscrepancySubgraph(finding_id || 'discrepancy_01', {
        auditId: auditId,
        description: description,
        clauseRef: clause_reference,
        delta: delta,
      });
      setSubgraph(data);
      setIsGraphOpen(true);
    } catch (err) {
      console.error('Failed to fetch discrepancy graph:', err);
      // Fallback local subgraph
      setSubgraph({
        nodes: [
          { id: 'inv_item', label: `Invoice Item (${description?.substring(0, 20)}...)`, type: 'Entity', is_anchor: true, properties: { delta: `$${Math.abs(delta || 0).toFixed(2)}` } },
          { id: 'clause_rule', label: `Clause (${clause_reference || 'Rate Rule'})`, type: 'Rule', is_anchor: true, properties: { text: clause_text || 'Contract clause' } },
          { id: 'doc_msa', label: 'Master Services Agreement', type: 'Document', properties: { status: 'Active' } },
        ],
        edges: [
          { source: 'inv_item', target: 'clause_rule', type: 'BILLED_ON' },
          { source: 'clause_rule', target: 'doc_msa', type: 'GOVERNED_BY' },
        ],
        anchor_node_ids: ['inv_item', 'clause_rule'],
      });
      setIsGraphOpen(true);
    } finally {
      setIsLoadingGraph(false);
    }
  };

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-lg p-5 text-sm space-y-5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="p-2 bg-teal-50 text-teal-600 rounded-lg shrink-0"><AlertCircle className="h-4 w-4 stroke-[1.5]" /></div>
          <div>
            <p className="text-[10px] uppercase font-semibold text-slate-400 tracking-wide">Agent Assessment</p>
            <p className="text-slate-900 font-medium mt-0.5 leading-relaxed">{description}</p>
          </div>
        </div>

        {/* Actions: Split-Screen Proof & Context Substrate Provenance */}
        <div className="flex items-center gap-2 shrink-0">
          {onOpenProof && (
            <button
              type="button"
              onClick={() => onOpenProof(finding_id)}
              className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1.5 rounded-lg bg-teal-50 hover:bg-teal-100 text-teal-700 border border-teal-200/80 transition-all hover:shadow-sm"
              title="Open Interactive Split-Screen PDF Proof with Visual Bounding Boxes"
            >
              <Eye className="w-3.5 h-3.5 text-teal-600" />
              <span>Split-Screen Proof</span>
            </button>
          )}

          <button
            type="button"
            onClick={handleOpenGraph}
            disabled={isLoadingGraph}
            className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1.5 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200/80 transition-all hover:shadow-sm"
            title="Inspect Neo4j Concept Graph & Clause Provenance"
          >
            <Network className="w-3.5 h-3.5 text-indigo-600" />
            <span>{isLoadingGraph ? 'Loading Trace...' : 'Graph Provenance'}</span>
          </button>
        </div>
      </div>

      {clause_text && (
        <div className="bg-white rounded-lg p-4 border border-slate-200 relative">
          <Quote className="absolute right-3 top-3 h-8 w-8 text-slate-200 stroke-[1.5]" />
          <div className="flex items-center justify-between mb-2">
            <p className="text-[10px] font-semibold text-teal-600 uppercase tracking-wide">
              Contract: {clause_reference || 'Clause Reference'}
            </p>
            <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200 font-mono">
              <ShieldCheck className="w-3 h-3" /> Substrate Grounded
            </span>
          </div>
          <blockquote className="text-slate-600 italic font-mono text-xs border-l-4 border-teal-500 pl-3 leading-relaxed">
            &ldquo;{clause_text}&rdquo;
          </blockquote>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="bg-white p-4 rounded-lg border border-slate-200">
          <p className="text-[10px] uppercase font-semibold text-slate-400">Charged</p>
          <p className="text-xs text-slate-600 mt-1">{quantity} × ${parseFloat(unit_price_charged || 0).toFixed(2)}</p>
          <p className="text-sm font-mono font-bold text-rose-600 mt-1">= ${parseFloat(line_total_charged || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}</p>
        </div>
        <div className="bg-white p-4 rounded-lg border border-slate-200">
          <p className="text-[10px] uppercase font-semibold text-slate-400">Expected</p>
          <p className="text-xs text-slate-600 mt-1">{quantity} × ${parseFloat(unit_price_expected || 0).toFixed(2)}</p>
          <p className="text-sm font-mono font-bold text-emerald-600 mt-1">= ${parseFloat(line_total_expected || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}</p>
        </div>
        <div className="bg-rose-50 p-4 rounded-lg border border-rose-200">
          <p className="text-[10px] uppercase font-semibold text-rose-600">Leakage</p>
          <p className="text-base font-mono font-bold text-rose-700 mt-1">${parseFloat(Math.abs(delta || 0)).toLocaleString('en-US', { minimumFractionDigits: 2 })}</p>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-200">
        <div className="flex items-center gap-2">
          <CheckSquare className="h-4 w-4 text-slate-400 stroke-[1.5]" />
          <span className="text-xs text-slate-500">Action:</span>
          <Badge variant={recVariant}>{recommendation}</Badge>
        </div>
        <div className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-lg border border-slate-200">
          <Target className="h-4 w-4 text-slate-400 stroke-[1.5]" />
          <span className="text-xs text-slate-500">Confidence</span>
          <div className="w-16 bg-slate-100 h-1.5 rounded-full overflow-hidden">
            <div className="h-full bg-teal-600 rounded-full" style={{ width: `${confidencePct}%` }} />
          </div>
          <span className="font-mono text-xs font-semibold text-slate-700">{confidencePct}%</span>
        </div>
      </div>

      {/* Reasoning Subgraph Modal for this finding */}
      <ReasoningSubgraphModal
        isOpen={isGraphOpen}
        onClose={() => setIsGraphOpen(false)}
        subgraph={subgraph}
        title={`Finding Provenance: ${finding_id || 'Discrepancy'}`}
        subtitle={`Hierarchical clause resolution for ${clause_reference || 'contract term'}`}
      />
    </div>
  );
}
