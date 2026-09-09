/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Interactive reasoning subgraph modal powered by SynaptAI Context Substrate.
 * Visualizes multi-hop graph traversals, semantic anchors, amendment supersessions, and clause paths.
 * 
 * What it means:
 * Unassailable explainability window. Lets auditors, legal teams, and CFOs visually verify
 * the exact knowledge path traversed to validate a clause or discrepancy.
 * 
 * Importance in Project:
 * High. Transforms black-box AI into a transparent, auditable, graph-grounded engine.
 */

import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  X,
  Search,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Sparkles,
  Info,
  Maximize2,
  Minimize2,
  ShieldCheck,
  Layers,
  ArrowRight,
  ExternalLink,
} from 'lucide-react';
import Modal from './ui/Modal';
import Badge from './ui/Badge';
import Button from './ui/Button';

// Node Type Theme Configuration
const TYPE_CONFIG = {
  Entity: { bg: '#3b82f6', border: '#1d4ed8', text: '#ffffff', label: 'Entity', pill: 'bg-blue-100 text-blue-800' },
  Concept: { bg: '#8b5cf6', border: '#6d28d9', text: '#ffffff', label: 'Concept', pill: 'bg-purple-100 text-purple-800' },
  Rule: { bg: '#10b981', border: '#047857', text: '#ffffff', label: 'Rule / Clause', pill: 'bg-emerald-100 text-emerald-800' },
  Chunk: { bg: '#f59e0b', border: '#b45309', text: '#ffffff', label: 'Chunk', pill: 'bg-amber-100 text-amber-800' },
  Document: { bg: '#64748b', border: '#334155', text: '#ffffff', label: 'Document', pill: 'bg-slate-100 text-slate-800' },
  Procedure: { bg: '#ec4899', border: '#be185d', text: '#ffffff', label: 'Procedure', pill: 'bg-pink-100 text-pink-800' },
  Step: { bg: '#06b6d4', border: '#0e7490', text: '#ffffff', label: 'Step', pill: 'bg-cyan-100 text-cyan-800' },
  Default: { bg: '#6b7280', border: '#374151', text: '#ffffff', label: 'Other', pill: 'bg-gray-100 text-gray-800' },
};

export default function ReasoningSubgraphModal({
  isOpen,
  onClose,
  title = 'Context Substrate: Reasoning Subgraph',
  subgraph,
  subtitle = 'Multi-hop graph traversal & semantic provenance trace',
}) {
  const [activeFilter, setActiveFilter] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [isFullscreen, setIsFullscreen] = useState(false);

  const containerRef = useRef(null);

  // Compute node coordinates using a robust radial/force-directed layout simulation
  const layout = useMemo(() => {
    if (!subgraph || !subgraph.nodes || subgraph.nodes.length === 0) {
      return { nodes: [], edges: [] };
    }

    const nodes = [...subgraph.nodes];
    const edges = [...(subgraph.edges || [])];
    const width = 800;
    const height = 500;
    const centerX = width / 2;
    const centerY = height / 2;

    const positionedNodes = nodes.map((node, index) => {
      const isAnchor = node.is_anchor || (subgraph.anchor_node_ids && subgraph.anchor_node_ids.includes(node.id));
      const total = nodes.length;
      
      // Place anchors near center; distribute others in concentric rings
      let radius = isAnchor ? 120 + (index % 2) * 30 : 200 + ((index * 37) % 110);
      let angle = (index / total) * 2 * Math.PI - Math.PI / 2;
      
      let x = centerX + radius * Math.cos(angle);
      let y = centerY + radius * Math.sin(angle);

      // Clamp inside viewport
      x = Math.max(60, Math.min(width - 60, x));
      y = Math.max(60, Math.min(height - 60, y));

      return {
        ...node,
        x,
        y,
        isAnchor,
      };
    });

    const nodeMap = new Map(positionedNodes.map((n) => [n.id, n]));

    const positionedEdges = edges
      .map((edge, idx) => {
        const sourceNode = nodeMap.get(edge.source);
        const targetNode = nodeMap.get(edge.target);
        if (!sourceNode || !targetNode) return null;
        return {
          ...edge,
          edgeId: `edge_${idx}`,
          sourceNode,
          targetNode,
        };
      })
      .filter(Boolean);

    return { nodes: positionedNodes, edges: positionedEdges };
  }, [subgraph]);

  // Filtering & search
  const filteredNodes = useMemo(() => {
    return layout.nodes.filter((node) => {
      const matchesType = activeFilter === 'ALL' || node.type.toUpperCase() === activeFilter.toUpperCase();
      const matchesSearch =
        !searchTerm ||
        node.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
        node.type.toLowerCase().includes(searchTerm.toLowerCase()) ||
        JSON.stringify(node.properties || {}).toLowerCase().includes(searchTerm.toLowerCase());
      return matchesType && matchesSearch;
    });
  }, [layout.nodes, activeFilter, searchTerm]);

  const selectedNode = useMemo(() => {
    if (!selectedNodeId) return null;
    return layout.nodes.find((n) => n.id === selectedNodeId);
  }, [selectedNodeId, layout.nodes]);

  // Connected edges for selected node
  const connectedEdges = useMemo(() => {
    if (!selectedNodeId) return [];
    return layout.edges.filter(
      (e) => e.source === selectedNodeId || e.target === selectedNodeId
    );
  }, [selectedNodeId, layout.edges]);

  // Zoom and Pan Handlers
  const handleMouseDown = (e) => {
    if (e.target.tagName === 'svg' || e.target.id === 'graph-viewport') {
      setIsDragging(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e) => {
    if (isDragging) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }
  };

  const handleMouseUp = () => setIsDragging(false);

  const resetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setSelectedNodeId(null);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/75 backdrop-blur-sm p-4 overflow-y-auto">
      <div
        className={`bg-white rounded-xl shadow-2xl border border-slate-200 flex flex-col overflow-hidden transition-all duration-300 ${
          isFullscreen ? 'w-full h-full max-w-none' : 'w-full max-w-6xl h-[88vh]'
        }`}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/80">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg border border-indigo-100">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-slate-900">{title}</h3>
                <span className="inline-flex items-center gap-1 text-[11px] font-semibold bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full border border-emerald-200">
                  <ShieldCheck className="w-3 h-3" /> SynaptAI Neo4j Concept Graph
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
              title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
            >
              {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>
            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Toolbar: Search, Filters & Zoom Controls */}
        <div className="px-6 py-2.5 border-b border-slate-100 bg-white flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 flex-1 max-w-sm">
            <div className="relative w-full">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search nodes, properties, or rules..."
                className="w-full pl-8 pr-3 py-1.5 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
              {searchTerm && (
                <button
                  onClick={() => setSearchTerm('')}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>
          </div>

          {/* Type Filter Pills */}
          <div className="flex items-center gap-1.5 flex-wrap">
            {['ALL', 'RULE', 'ENTITY', 'CONCEPT', 'DOCUMENT', 'CHUNK'].map((type) => (
              <button
                key={type}
                onClick={() => setActiveFilter(type)}
                className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors ${
                  activeFilter === type
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {type}
              </button>
            ))}
          </div>

          {/* View Controls */}
          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg">
            <button
              onClick={() => setZoom((z) => Math.min(z + 0.2, 2.4))}
              className="p-1 hover:bg-white rounded text-slate-600"
              title="Zoom In"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
            <span className="text-[10px] font-mono font-medium px-1 text-slate-500">
              {Math.round(zoom * 100)}%
            </span>
            <button
              onClick={() => setZoom((z) => Math.max(z - 0.2, 0.4))}
              className="p-1 hover:bg-white rounded text-slate-600"
              title="Zoom Out"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <div className="w-px h-3 bg-slate-200 mx-0.5" />
            <button
              onClick={resetView}
              className="p-1 hover:bg-white rounded text-slate-600"
              title="Reset View"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Graph Canvas & Side Inspector */}
        <div className="flex-1 flex overflow-hidden relative" ref={containerRef}>
          {/* Interactive SVG Canvas */}
          <div
            id="graph-viewport"
            className="flex-1 bg-gradient-to-br from-slate-50 to-slate-100/50 cursor-grab active:cursor-grabbing relative overflow-hidden select-none"
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
          >
            <svg
              className="w-full h-full"
              viewBox="0 0 800 500"
              style={{
                transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
                transformOrigin: 'center center',
              }}
            >
              <defs>
                {/* Arrow markers */}
                <marker
                  id="arrow-default"
                  viewBox="0 -5 10 10"
                  refX="28"
                  refY="0"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto"
                >
                  <path d="M0,-5L10,0L0,5" fill="#94a3b8" />
                </marker>
                <marker
                  id="arrow-supersedes"
                  viewBox="0 -5 10 10"
                  refX="28"
                  refY="0"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto"
                >
                  <path d="M0,-5L10,0L0,5" fill="#ef4444" />
                </marker>
                <marker
                  id="arrow-governed"
                  viewBox="0 -5 10 10"
                  refX="28"
                  refY="0"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto"
                >
                  <path d="M0,-5L10,0L0,5" fill="#10b981" />
                </marker>

                {/* Pulsing glow filter for anchor nodes */}
                <filter id="anchor-glow" x="-50%" y="-50%" width="200%" height="200%">
                  <feGaussianBlur stdDeviation="6" result="blur" />
                  <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
              </defs>

              {/* Render Edges */}
              <g className="edges-layer">
                {layout.edges.map((edge) => {
                  const isSupersedes = edge.type === 'SUPERSEDES';
                  const isGoverned = edge.type === 'GOVERNED_BY';
                  const strokeColor = isSupersedes ? '#ef4444' : isGoverned ? '#10b981' : '#cbd5e1';
                  const markerId = isSupersedes ? 'url(#arrow-supersedes)' : isGoverned ? 'url(#arrow-governed)' : 'url(#arrow-default)';

                  const midX = (edge.sourceNode.x + edge.targetNode.x) / 2;
                  const midY = (edge.sourceNode.y + edge.targetNode.y) / 2;

                  return (
                    <g key={edge.edgeId}>
                      <line
                        x1={edge.sourceNode.x}
                        y1={edge.sourceNode.y}
                        x2={edge.targetNode.x}
                        y2={edge.targetNode.y}
                        stroke={strokeColor}
                        strokeWidth={isSupersedes ? 2.5 : 1.75}
                        strokeDasharray={isSupersedes ? '4,4' : 'none'}
                        markerEnd={markerId}
                      />
                      {/* Edge Label Badge */}
                      <rect
                        x={midX - 28}
                        y={midY - 8}
                        width="56"
                        height="16"
                        rx="4"
                        fill="white"
                        stroke={strokeColor}
                        strokeWidth="1"
                        className="opacity-90"
                      />
                      <text
                        x={midX}
                        y={midY + 3.5}
                        textAnchor="middle"
                        fontSize="8.5"
                        fontWeight="600"
                        fill={isSupersedes ? '#dc2626' : '#475569'}
                        className="pointer-events-none uppercase font-mono"
                      >
                        {edge.type}
                      </text>
                    </g>
                  );
                })}
              </g>

              {/* Render Nodes */}
              <g className="nodes-layer">
                {filteredNodes.map((node) => {
                  const typeCfg = TYPE_CONFIG[node.type] || TYPE_CONFIG.Default;
                  const isSelected = selectedNodeId === node.id;
                  const isAnchor = node.isAnchor;

                  return (
                    <g
                      key={node.id}
                      transform={`translate(${node.x}, ${node.y})`}
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedNodeId(node.id);
                      }}
                      className="cursor-pointer group"
                    >
                      {/* Anchor Pulsing Ring */}
                      {isAnchor && (
                        <circle
                          r="26"
                          fill="none"
                          stroke="#6366f1"
                          strokeWidth="2"
                          strokeOpacity="0.4"
                          className="animate-ping"
                        />
                      )}

                      {/* Selection Ring */}
                      {isSelected && (
                        <circle
                          r="25"
                          fill="none"
                          stroke="#1e293b"
                          strokeWidth="2.5"
                          strokeDasharray="3,3"
                        />
                      )}

                      {/* Main Node Circle */}
                      <circle
                        r="18"
                        fill={typeCfg.bg}
                        stroke={isAnchor ? '#4338ca' : typeCfg.border}
                        strokeWidth={isAnchor ? 3 : 2}
                        filter={isAnchor ? 'url(#anchor-glow)' : undefined}
                        className="transition-transform duration-200 group-hover:scale-110"
                      />

                      {/* Node Icon / Initial */}
                      <text
                        textAnchor="middle"
                        dy="4"
                        fill="#ffffff"
                        fontSize="10"
                        fontWeight="700"
                        className="pointer-events-none"
                      >
                        {node.type === 'Rule'
                          ? '§'
                          : node.type === 'Entity'
                          ? 'E'
                          : node.type === 'Concept'
                          ? 'C'
                          : node.type === 'Document'
                          ? 'D'
                          : '•'}
                      </text>

                      {/* Node Label Below */}
                      <rect
                        x="-55"
                        y="23"
                        width="110"
                        height="18"
                        rx="4"
                        fill="white"
                        stroke="#e2e8f0"
                        strokeWidth="1"
                        className="shadow-sm opacity-95 group-hover:opacity-100"
                      />
                      <text
                        x="0"
                        y="35"
                        textAnchor="middle"
                        fontSize="9"
                        fontWeight="600"
                        fill="#1e293b"
                        className="pointer-events-none truncate"
                      >
                        {node.label.length > 20 ? `${node.label.substring(0, 18)}...` : node.label}
                      </text>

                      {isAnchor && (
                        <text
                          x="0"
                          y="50"
                          textAnchor="middle"
                          fontSize="7.5"
                          fontWeight="700"
                          fill="#4f46e5"
                          className="uppercase tracking-wider font-mono"
                        >
                          ★ Semantic Anchor
                        </text>
                      )}
                    </g>
                  );
                })}
              </g>
            </svg>

            {/* Canvas Legend */}
            <div className="absolute bottom-3 left-3 bg-white/90 backdrop-blur-sm border border-slate-200 rounded-lg p-2.5 shadow-sm text-[11px] space-y-1.5 pointer-events-auto">
              <div className="font-semibold text-slate-700 flex items-center gap-1.5 mb-1 text-[10px] uppercase tracking-wider">
                <Layers className="w-3 h-3 text-indigo-500" /> Graph Schema Legend
              </div>
              <div className="grid grid-cols-2 gap-x-3 gap-y-1">
                {Object.entries(TYPE_CONFIG).slice(0, 6).map(([key, cfg]) => (
                  <div key={key} className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: cfg.bg }} />
                    <span className="text-slate-600 text-[10px]">{cfg.label}</span>
                  </div>
                ))}
              </div>
              <div className="border-t border-slate-100 pt-1.5 mt-1.5 flex items-center gap-2 text-[10px] text-slate-500">
                <span className="text-red-500 font-bold">---&gt;</span> SUPERSEDES
                <span className="text-emerald-500 font-bold font-mono">──&gt;</span> GOVERNED_BY
              </div>
            </div>
          </div>

          {/* Node Inspector Drawer */}
          {selectedNode ? (
            <div className="w-80 border-l border-slate-200 bg-white p-5 flex flex-col justify-between overflow-y-auto shadow-lg animate-in slide-in-from-right duration-200">
              <div className="space-y-4">
                <div className="flex items-start justify-between">
                  <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded ${TYPE_CONFIG[selectedNode.type]?.pill || 'bg-slate-100'}`}>
                    {selectedNode.type}
                  </span>
                  <button
                    onClick={() => setSelectedNodeId(null)}
                    className="text-slate-400 hover:text-slate-600 p-1"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                <div>
                  <h4 className="font-bold text-slate-900 text-sm leading-snug">{selectedNode.label}</h4>
                  <p className="text-[10px] font-mono text-slate-400 mt-0.5">ID: {selectedNode.id}</p>
                </div>

                {selectedNode.isAnchor && (
                  <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-2.5 text-xs text-indigo-800 flex items-start gap-2">
                    <Sparkles className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold">Semantic Search Anchor</span>
                      <p className="text-[11px] text-indigo-700 mt-0.5">
                        Identified directly via Milvus GN vector index without fuzzy text lookup.
                      </p>
                    </div>
                  </div>
                )}

                {/* Node Properties */}
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-2">Properties</p>
                  <div className="bg-slate-50 rounded-lg p-3 border border-slate-100 space-y-2 text-xs">
                    {Object.entries(selectedNode.properties || {}).length === 0 ? (
                      <p className="text-slate-400 italic text-[11px]">No custom properties recorded</p>
                    ) : (
                      Object.entries(selectedNode.properties || {}).map(([k, v]) => (
                        <div key={k} className="flex flex-col">
                          <span className="text-[10px] font-medium text-slate-500 uppercase">{k.replace(/_/g, ' ')}</span>
                          <span className="text-slate-800 font-medium break-words mt-0.5">{String(v)}</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Connected Relationships */}
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-2">
                    Connected Relationships ({connectedEdges.length})
                  </p>
                  <div className="space-y-1.5 max-h-48 overflow-y-auto">
                    {connectedEdges.map((e) => {
                      const isOutgoing = e.source === selectedNode.id;
                      const otherNodeId = isOutgoing ? e.target : e.source;
                      const otherNode = layout.nodes.find((n) => n.id === otherNodeId);

                      return (
                        <div
                          key={e.edgeId}
                          onClick={() => setSelectedNodeId(otherNodeId)}
                          className="p-2 rounded-lg bg-slate-50 hover:bg-slate-100 border border-slate-100 cursor-pointer transition-colors text-xs flex items-center justify-between"
                        >
                          <div className="flex items-center gap-1.5 truncate">
                            <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 bg-white rounded border border-slate-200 text-slate-600">
                              {e.type}
                            </span>
                            <span className="text-slate-700 truncate font-medium">{otherNode?.label || otherNodeId}</span>
                          </div>
                          <ArrowRight className="w-3 h-3 text-slate-400 shrink-0" />
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-100 text-[11px] text-slate-400 flex items-center justify-between">
                <span>Neo4j Graph Engine</span>
                <span className="font-mono">TriStore v2.1</span>
              </div>
            </div>
          ) : (
            <div className="w-72 border-l border-slate-200 bg-slate-50/50 p-6 flex flex-col items-center justify-center text-center text-slate-400">
              <Info className="w-8 h-8 stroke-1 text-slate-300 mb-2" />
              <p className="text-xs font-medium text-slate-600">Select any node</p>
              <p className="text-[11px] text-slate-400 mt-1 max-w-[200px]">
                Click a rule, entity, or chunk on the canvas to inspect properties, verbatim text, and relationships.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
