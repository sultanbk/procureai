/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * 3-Step Wizard Modal to create and register a new SynaptAI Context Provider.
 * Step 1: Provider Identity & Knowledge Pack (extraction mode, packets, entity & relationship types)
 * Step 2: Context Scope (stores included, entity types exposed, depth hops limit, max results)
 * Step 3: Client ID & Access Control (rate limit, token TTL, target platform)
 * 
 * What it means:
 * Knowledge base provisioner. Partitions Neo4j subgraphs and Milvus collections per enterprise client.
 * 
 * Importance in Project:
 * High. Direct implementation of the SynaptAI Context Substrate Provider specification.
 */

import React, { useState } from 'react';
import {
  X,
  Layers,
  Sparkles,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  Database,
  Network,
  GitBranch,
  Key,
  ShieldCheck,
  RefreshCw,
  Copy,
  Check,
  Server,
  Terminal,
  Cpu,
  Globe,
} from 'lucide-react';
import Button from './ui/Button';
import Spinner from './ui/Spinner';
import { createContextProvider } from '../api';

const PACKETS = [
  { id: 'default', label: 'default', desc: 'Standard procurement & enterprise contracts' },
  { id: 'clougovernance', label: 'clougovernance', desc: 'Cloud infrastructure, CIS benchmarks & policies' },
  { id: 'cobol_ingestion', label: 'cobol_ingestion', desc: 'Legacy COBOL data definition & ingestion' },
  { id: 'cobol_source code', label: 'cobol_source code', desc: 'COBOL copybooks & procedure division' },
  { id: 'incidenthandling', label: 'incidenthandling', desc: 'SRE & security incident runbooks' },
  { id: 'learningpack', label: 'learningpack', desc: 'Enterprise onboarding & knowledge training' },
  { id: 'minitoring', label: 'minitoring', desc: 'Observability, latency & SLA monitoring' },
  { id: 'source code', label: 'source code', desc: 'General programming languages & AST' },
  { id: 'test_pack_003', label: 'test_pack_003', desc: 'Automated test suite & regression fixtures' },
  { id: 'vehicle pack', label: 'vehicle pack', desc: 'Fleet telematics & transportation specs' },
];

const EXTRACTION_MODES = [
  { id: 'balanced', label: 'Balanced (Default)', desc: 'Balanced coverage vs speed. Recommended for most documents.' },
  { id: 'fast', label: 'Fast', desc: 'Fewest passes, captures only primary entities.' },
  { id: 'max_extraction', label: 'Max Extraction', desc: 'Extracts every entity, concept and edge.' },
  { id: 'deep', label: 'Deep Reasoning', desc: 'Multi-pass thorough reasoning for complex contracts.' },
  { id: 'fact_dense', label: 'Fact Dense', desc: 'Dense factual triples for technical specifications.' },
  { id: 'precise', label: 'Precise', desc: 'High-precision with strict confidence filtering.' },
  { id: 'auto', label: 'Auto Preset', desc: 'Automatically selects preset based on document type.' },
];

const TARGET_PLATFORMS = [
  { id: 'langgraph', label: 'LangGraph', desc: 'Stateful multi-agent compliance pipeline', icon: Cpu },
  { id: 'agentcraft', label: 'AgentCraft', desc: 'Autonomous agentic workflow orchestrator', icon: Terminal },
  { id: 'crewai', label: 'CrewAI', desc: 'Role-based collaborative agent squads', icon: Server },
  { id: 'custom api', label: 'Custom API', desc: 'Direct REST/gRPC client integration', icon: Globe },
];

export default function CreateProviderModal({ isOpen, onClose, onCreated }) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [copiedClientId, setCopiedClientId] = useState(false);

  // Form State: Step 1
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [extractionMode, setExtractionMode] = useState('balanced');
  const [knowledgePackSource, setKnowledgePackSource] = useState('system-defined-types');
  const [knowledgePackPacket, setKnowledgePackPacket] = useState('default');
  const [entityTypes, setEntityTypes] = useState([
    'Organization', 'Vendor', 'Customer', 'Contract', 'Rule', 'SLA', 'Policy'
  ]);
  const [newEntityType, setNewEntityType] = useState('');
  const [relationshipTypes, setRelationshipTypes] = useState([
    'GOVERNED_BY', 'DEFINES', 'SUPERSEDES', 'BILLED_ON', 'PRECEDES', 'HAS_STEP'
  ]);
  const [newRelType, setNewRelType] = useState('');

  // Form State: Step 2
  const [storesIncluded, setStoresIncluded] = useState([
    'Knowledge Store (Milvus KS)',
    'Context Graph (Neo4j)',
    'Procedure Store (Milvus PS)'
  ]);
  const [entityTypesExposed, setEntityTypesExposed] = useState([
    'customer', 'order', 'product', 'policy'
  ]);
  const [contextDepthLimit, setContextDepthLimit] = useState(2);
  const [maxResultsPerQuery, setMaxResultsPerQuery] = useState(50);

  // Form State: Step 3
  const [clientId, setClientId] = useState(`client_${Math.random().toString(36).substring(2, 12)}_${Date.now().toString(36)}`);
  const [rateLimitRpm, setRateLimitRpm] = useState(120);
  const [tokenTtlHours, setTokenTtlHours] = useState(24);
  const [targetPlatform, setTargetPlatform] = useState('langgraph');

  if (!isOpen) return null;

  const generateNewClientId = () => {
    setClientId(`client_${Math.random().toString(36).substring(2, 12)}_${Date.now().toString(36)}`);
  };

  const handleCopyClientId = () => {
    navigator.clipboard.writeText(clientId);
    setCopiedClientId(true);
    setTimeout(() => setCopiedClientId(false), 2000);
  };

  const toggleStore = (storeName) => {
    if (storesIncluded.includes(storeName)) {
      if (storesIncluded.length === 1) return; // keep at least 1
      setStoresIncluded(storesIncluded.filter((s) => s !== storeName));
    } else {
      setStoresIncluded([...storesIncluded, storeName]);
    }
  };

  const toggleExposedEntity = (ent) => {
    if (entityTypesExposed.includes(ent)) {
      setEntityTypesExposed(entityTypesExposed.filter((e) => e !== ent));
    } else {
      setEntityTypesExposed([...entityTypesExposed, ent]);
    }
  };

  const handleAddEntityType = () => {
    if (!newEntityType.trim()) return;
    if (!entityTypes.includes(newEntityType.trim())) {
      setEntityTypes([...entityTypes, newEntityType.trim()]);
    }
    setNewEntityType('');
  };

  const handleRemoveEntityType = (t) => {
    setEntityTypes(entityTypes.filter((x) => x !== t));
  };

  const handleAddRelType = () => {
    if (!newRelType.trim()) return;
    const formatted = newRelType.trim().toUpperCase().replace(/[^A-Z0-9_]/g, '_');
    if (!relationshipTypes.includes(formatted)) {
      setRelationshipTypes([...relationshipTypes, formatted]);
    }
    setNewRelType('');
  };

  const handleRemoveRelType = (t) => {
    setRelationshipTypes(relationshipTypes.filter((x) => x !== t));
  };

  const handleNext = (e) => {
    e.preventDefault();
    if (step === 1) {
      if (!name.trim()) {
        setError('Provider name is required.');
        return;
      }
      setError(null);
      setStep(2);
    } else if (step === 2) {
      if (storesIncluded.length === 0) {
        setError('At least one store must be included.');
        return;
      }
      setError(null);
      setStep(3);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const payload = {
      name: name.trim(),
      description: description.trim(),
      extraction_mode: extractionMode,
      knowledge_pack_source: knowledgePackSource,
      knowledge_pack_packet: knowledgePackPacket,
      entity_types: entityTypes,
      relationship_types: relationshipTypes,
      stores_included: storesIncluded,
      entity_types_exposed: entityTypesExposed,
      context_depth_limit: parseInt(contextDepthLimit) || 2,
      max_results_per_query: parseInt(maxResultsPerQuery) || 50,
      client_id: clientId,
      rate_limit_rpm: parseInt(rateLimitRpm) || 120,
      token_ttl_hours: parseInt(tokenTtlHours) || 24,
      target_platform: targetPlatform,
    };

    try {
      const created = await createContextProvider(payload);
      if (onCreated) onCreated(created);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to create Context Provider.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/75 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-3xl overflow-hidden flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-50 text-indigo-600 rounded-xl border border-indigo-100">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Create Context Provider</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Provision an isolated knowledge base with dedicated Neo4j subgraphs &amp; Milvus vector stores
              </p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Step Indicator Stepper */}
        <div className="px-6 py-3 bg-white border-b border-slate-100 flex items-center justify-between text-xs">
          {[
            { num: 1, label: 'Identity & Knowledge Pack' },
            { num: 2, label: 'Context Scope & Limits' },
            { num: 3, label: 'Client ID & Access' },
          ].map((s, idx) => (
            <div key={s.num} className="flex items-center gap-2">
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center font-bold text-[11px] transition-colors ${
                  step === s.num
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : step > s.num
                    ? 'bg-emerald-500 text-white'
                    : 'bg-slate-100 text-slate-500'
                }`}
              >
                {step > s.num ? <Check className="w-3.5 h-3.5" /> : s.num}
              </div>
              <span
                className={`font-medium ${
                  step === s.num ? 'text-indigo-600 font-bold' : 'text-slate-500'
                }`}
              >
                {s.label}
              </span>
              {idx < 2 && <div className="w-8 sm:w-12 h-px bg-slate-200 ml-2" />}
            </div>
          ))}
        </div>

        {/* Form Body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-5">
          {error && (
            <div className="bg-rose-50 border border-rose-200 text-rose-700 px-4 py-2.5 rounded-lg text-xs font-medium">
              {error}
            </div>
          )}

          {/* ========================================================================= */}
          {/* STEP 1: Provider Identity & Knowledge Pack */}
          {/* ========================================================================= */}
          {step === 1 && (
            <div className="space-y-4 animate-in fade-in duration-150">
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                  Provider Name <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Apex Telecom Knowledge Substrate"
                  className="w-full px-3.5 py-2 border border-slate-200 rounded-lg text-xs focus:ring-1 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                  Description
                </label>
                <textarea
                  rows={2}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="e.g. Knowledge base covering telecom circuits, amendment hierarchies, and recovery playbooks."
                  className="w-full px-3.5 py-2 border border-slate-200 rounded-lg text-xs focus:ring-1 focus:ring-indigo-500 focus:outline-none resize-none"
                />
              </div>

              {/* Extraction Mode */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                  Extraction Mode Preset
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {EXTRACTION_MODES.slice(0, 6).map((m) => (
                    <div
                      key={m.id}
                      onClick={() => setExtractionMode(m.id)}
                      className={`p-2.5 rounded-lg border text-xs cursor-pointer transition-all ${
                        extractionMode === m.id
                          ? 'border-indigo-600 bg-indigo-50/50 shadow-sm'
                          : 'border-slate-200 hover:border-slate-300 bg-white'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-900 text-xs">{m.label}</span>
                        {extractionMode === m.id && (
                          <CheckCircle2 className="w-3.5 h-3.5 text-indigo-600" />
                        )}
                      </div>
                      <p className="text-[11px] text-slate-500 mt-1 leading-snug">{m.desc}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Knowledge Pack Configuration */}
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-3.5">
                <div className="flex items-center justify-between border-b border-slate-200/80 pb-2">
                  <span className="text-xs font-bold text-slate-800 uppercase tracking-wide">
                    Knowledge Pack Configuration
                  </span>
                  {/* Source Toggle: system-defined-types vs user-defined */}
                  <div className="inline-flex p-0.5 bg-white border border-slate-200 rounded-lg text-[11px]">
                    <button
                      type="button"
                      onClick={() => setKnowledgePackSource('system-defined-types')}
                      className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                        knowledgePackSource === 'system-defined-types'
                          ? 'bg-indigo-600 text-white shadow-sm font-bold'
                          : 'text-slate-600 hover:text-slate-800'
                      }`}
                    >
                      system-defined-types
                    </button>
                    <button
                      type="button"
                      onClick={() => setKnowledgePackSource('user-defined')}
                      className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                        knowledgePackSource === 'user-defined'
                          ? 'bg-indigo-600 text-white shadow-sm font-bold'
                          : 'text-slate-600 hover:text-slate-800'
                      }`}
                    >
                      user-defined
                    </button>
                  </div>
                </div>

                {/* Packet Selection */}
                <div className="space-y-1.5">
                  <label className="text-[11px] font-bold text-slate-600 uppercase tracking-wide">
                    Packet Template
                  </label>
                  <select
                    value={knowledgePackPacket}
                    onChange={(e) => setKnowledgePackPacket(e.target.value)}
                    className="w-full px-3 py-1.5 border border-slate-200 bg-white rounded-lg text-xs focus:ring-1 focus:ring-indigo-500"
                  >
                    {PACKETS.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.label} — {p.desc}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Entity Types Tags */}
                <div className="space-y-1.5">
                  <label className="text-[11px] font-bold text-slate-600 uppercase tracking-wide">
                    Entity Types Taxonomy
                  </label>
                  <div className="flex flex-wrap gap-1.5 items-center">
                    {entityTypes.map((t) => (
                      <span
                        key={t}
                        className="inline-flex items-center gap-1 text-[11px] font-medium bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded-md"
                      >
                        {t}
                        <button
                          type="button"
                          onClick={() => handleRemoveEntityType(t)}
                          className="hover:text-blue-900"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </span>
                    ))}
                    <div className="flex items-center gap-1">
                      <input
                        type="text"
                        value={newEntityType}
                        onChange={(e) => setNewEntityType(e.target.value)}
                        placeholder="+ Add type..."
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault();
                            handleAddEntityType();
                          }
                        }}
                        className="px-2 py-0.5 border border-slate-200 rounded text-[11px] w-24 focus:outline-none"
                      />
                    </div>
                  </div>
                </div>

                {/* Relationship Types Tags */}
                <div className="space-y-1.5">
                  <label className="text-[11px] font-bold text-slate-600 uppercase tracking-wide">
                    Relationship Types (Predicates)
                  </label>
                  <div className="flex flex-wrap gap-1.5 items-center">
                    {relationshipTypes.map((r) => (
                      <span
                        key={r}
                        className="inline-flex items-center gap-1 text-[11px] font-mono font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-md"
                      >
                        {r}
                        <button
                          type="button"
                          onClick={() => handleRemoveRelType(r)}
                          className="hover:text-emerald-900"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </span>
                    ))}
                    <div className="flex items-center gap-1">
                      <input
                        type="text"
                        value={newRelType}
                        onChange={(e) => setNewRelType(e.target.value)}
                        placeholder="+ Add edge..."
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault();
                            handleAddRelType();
                          }
                        }}
                        className="px-2 py-0.5 border border-slate-200 rounded text-[11px] w-24 font-mono focus:outline-none"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ========================================================================= */}
          {/* STEP 2: Context Scope & Limits */}
          {/* ========================================================================= */}
          {step === 2 && (
            <div className="space-y-5 animate-in fade-in duration-150">
              {/* Stores Included */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                  Stores Included in Namespace
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {[
                    { id: 'Knowledge Store (Milvus KS)', label: 'Knowledge Store', store: 'Milvus KS', icon: Database },
                    { id: 'Context Graph (Neo4j)', label: 'Context Graph', store: 'Neo4j Concept', icon: Network },
                    { id: 'Procedure Store (Milvus PS)', label: 'Procedure Store', store: 'Milvus PS (DAG)', icon: GitBranch },
                  ].map((store) => {
                    const isChecked = storesIncluded.includes(store.id);
                    const Icon = store.icon;
                    return (
                      <div
                        key={store.id}
                        onClick={() => toggleStore(store.id)}
                        className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                          isChecked
                            ? 'border-indigo-600 bg-indigo-50/40 shadow-sm'
                            : 'border-slate-200 bg-slate-50/50 hover:bg-slate-100 opacity-60'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1.5">
                          <Icon className={`w-4 h-4 ${isChecked ? 'text-indigo-600' : 'text-slate-400'}`} />
                          <div
                            className={`w-4 h-4 rounded border flex items-center justify-center ${
                              isChecked ? 'bg-indigo-600 border-indigo-600 text-white' : 'border-slate-300'
                            }`}
                          >
                            {isChecked && <Check className="w-3 h-3" />}
                          </div>
                        </div>
                        <p className="text-xs font-bold text-slate-900">{store.label}</p>
                        <p className="text-[10px] font-mono text-slate-500 mt-0.5">{store.store}</p>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Entity Types Exposed */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                  Entity Types Exposed to Consumer Agents
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {['customer', 'order', 'product', 'policy'].map((ent) => {
                    const isExposed = entityTypesExposed.includes(ent);
                    return (
                      <button
                        type="button"
                        key={ent}
                        onClick={() => toggleExposedEntity(ent)}
                        className={`px-3 py-2 rounded-lg border text-xs font-semibold capitalize flex items-center justify-between transition-colors ${
                          isExposed
                            ? 'bg-purple-50 text-purple-800 border-purple-300 shadow-sm'
                            : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                        }`}
                      >
                        <span>{ent}</span>
                        {isExposed && <Check className="w-3.5 h-3.5 text-purple-600" />}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Sliders / Limits: Depth Limit & Max Results */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-800 uppercase tracking-wide">
                      Context Depth Limit
                    </span>
                    <span className="font-mono font-bold text-indigo-600 text-xs px-2 py-0.5 bg-indigo-50 border border-indigo-100 rounded">
                      {contextDepthLimit} hops
                    </span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    value={contextDepthLimit}
                    onChange={(e) => setContextDepthLimit(e.target.value)}
                    className="w-full accent-indigo-600 cursor-pointer"
                  />
                  <p className="text-[11px] text-slate-500">
                    Maximum multi-hop BFS neighborhood expansion from semantic anchor nodes.
                  </p>
                </div>

                <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-800 uppercase tracking-wide">
                      Max Results Per Query
                    </span>
                    <span className="font-mono font-bold text-indigo-600 text-xs px-2 py-0.5 bg-indigo-50 border border-indigo-100 rounded">
                      {maxResultsPerQuery} items
                    </span>
                  </div>
                  <input
                    type="range"
                    min="10"
                    max="100"
                    step="5"
                    value={maxResultsPerQuery}
                    onChange={(e) => setMaxResultsPerQuery(e.target.value)}
                    className="w-full accent-indigo-600 cursor-pointer"
                  />
                  <p className="text-[11px] text-slate-500">
                    Top-K semantic chunks and entity graph nodes retrieved into context.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* ========================================================================= */}
          {/* STEP 3: Client ID & Access Control */}
          {/* ========================================================================= */}
          {step === 3 && (
            <div className="space-y-4 animate-in fade-in duration-150">
              {/* Generated Client ID */}
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-700 uppercase tracking-wide flex items-center gap-1.5">
                    <Key className="w-3.5 h-3.5 text-amber-500" />
                    Substrate Client ID (S2S Credential)
                  </span>
                  <button
                    type="button"
                    onClick={generateNewClientId}
                    className="text-[11px] text-slate-500 hover:text-indigo-600 flex items-center gap-1 font-semibold"
                  >
                    <RefreshCw className="w-3 h-3" /> Regenerate
                  </button>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    readOnly
                    value={clientId}
                    className="w-full font-mono text-xs px-3 py-2 bg-white border border-slate-200 rounded-lg text-slate-800 font-bold"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={handleCopyClientId}
                    className="shrink-0 flex items-center gap-1"
                  >
                    {copiedClientId ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiedClientId ? 'Copied' : 'Copy'}</span>
                  </Button>
                </div>
                <p className="text-[11px] text-slate-500">
                  Used by agent platforms and API gateways to scope all queries to this provider namespace.
                </p>
              </div>

              {/* Rate Limit & Token TTL */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                    Rate Limit (Requests / Minute)
                  </label>
                  <input
                    type="number"
                    value={rateLimitRpm}
                    onChange={(e) => setRateLimitRpm(e.target.value)}
                    className="w-full px-3.5 py-2 border border-slate-200 rounded-lg text-xs font-mono focus:ring-1 focus:ring-indigo-500"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                    Token TTL (Hours)
                  </label>
                  <input
                    type="number"
                    value={tokenTtlHours}
                    onChange={(e) => setTokenTtlHours(e.target.value)}
                    className="w-full px-3.5 py-2 border border-slate-200 rounded-lg text-xs font-mono focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
              </div>

              {/* Target Platform Selector */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                  Target Agentic Platform
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {TARGET_PLATFORMS.map((plat) => {
                    const isSelected = targetPlatform === plat.id;
                    const Icon = plat.icon;
                    return (
                      <div
                        key={plat.id}
                        onClick={() => setTargetPlatform(plat.id)}
                        className={`p-3 rounded-xl border cursor-pointer transition-all ${
                          isSelected
                            ? 'border-indigo-600 bg-indigo-50/50 shadow-sm'
                            : 'border-slate-200 bg-white hover:border-slate-300'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <div className="p-1 bg-white border border-slate-200 rounded text-slate-700">
                              <Icon className="w-3.5 h-3.5" />
                            </div>
                            <span className="font-bold text-xs text-slate-900">{plat.label}</span>
                          </div>
                          {isSelected && <CheckCircle2 className="w-4 h-4 text-indigo-600" />}
                        </div>
                        <p className="text-[11px] text-slate-500 mt-1 leading-snug">{plat.desc}</p>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer Navigation Controls */}
        <div className="px-6 py-4 border-t border-slate-100 bg-slate-50 flex items-center justify-between">
          <div>
            {step > 1 ? (
              <Button
                type="button"
                variant="outline"
                onClick={() => setStep(step - 1)}
                className="flex items-center gap-1.5 text-xs font-bold"
              >
                <ArrowLeft className="w-3.5 h-3.5" /> Back
              </Button>
            ) : (
              <Button type="button" variant="outline" onClick={onClose} className="text-xs font-medium">
                Cancel
              </Button>
            )}
          </div>

          <div>
            {step < 3 ? (
              <Button
                type="button"
                onClick={handleNext}
                className="flex items-center gap-1.5 text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white"
              >
                Next Step <ArrowRight className="w-3.5 h-3.5" />
              </Button>
            ) : (
              <Button
                type="button"
                disabled={loading}
                onClick={handleSubmit}
                className="flex items-center gap-1.5 text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm"
              >
                {loading ? <Spinner size="sm" /> : <ShieldCheck className="w-4 h-4" />}
                <span>{loading ? 'Provisioning Substrate...' : 'Create Provider'}</span>
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
