/**
 * ProcureAI - File Summary
 *
 * What it does:
 * Interactive panel allowing users to chat with contracts.
 *
 * What it means:
 * Legal assistant interface.
 *
 * Importance in Project:
 * High. Allows users to query complex clauses without scrolling PDFs.
 */

import { useEffect, useRef, useState } from 'react';
import { Bot, ChevronRight, FileText, Loader2, Send, Sparkles, X } from 'lucide-react';
import { chatWithContract } from '../api';
import Drawer from './ui/Drawer';

const DELIMITER = '\n\n---CITATIONS---\n';

const suggestedQuestions = [
  "What's our unit price for 1,000 units?",
  'When does the SLA penalty apply?',
  'Is there an early payment discount?',
  "What's the contract period?",
];

function parseStreamPayload(rawText) {
  const [answerPart, metadataPart] = rawText.split(DELIMITER);
  let answer = answerPart || '';
  let metadata = null;

  if (metadataPart) {
    try {
      metadata = JSON.parse(metadataPart);
      answer = metadata.answer || answer;
    } catch {
      metadata = null;
    }
  }

  const confidenceMatch = answer.match(/\[CONFIDENCE:\s*(HIGH|MEDIUM|NOT_FOUND)\]/i);
  const confidence = metadata?.confidence
    ? metadata.confidence.toUpperCase()
    : confidenceMatch?.[1]?.toUpperCase() || '';

  return {
    content: answer.replace(/\[CONFIDENCE:\s*(HIGH|MEDIUM|NOT_FOUND)\]/i, '').trim(),
    confidence,
    citations: metadata?.citations || [],
  };
}

function confidenceLabel(confidence) {
  if (confidence === 'HIGH') return 'High confidence';
  if (confidence === 'MEDIUM') return 'Inferred from contract';
  return 'Not found in contract';
}

function confidenceDotClass(confidence) {
  if (confidence === 'HIGH') return 'bg-emerald-500';
  if (confidence === 'MEDIUM') return 'bg-amber-400';
  return 'bg-slate-300';
}

export default function ContractQADrawer({ isOpen, onClose, auditId, supplierName }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [openCitations, setOpenCitations] = useState({});
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const updateAssistantMessage = (id, patch) => {
    setMessages((prev) =>
      prev.map((message) => (message.id === id ? { ...message, ...patch } : message))
    );
  };

  const handleSend = async (textToSend) => {
    const query = (textToSend || input).trim();
    if (!query || isLoading) return;

    const userMessage = { id: crypto.randomUUID(), role: 'user', content: query };
    const assistantMessage = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      confidence: '',
      citations: [],
    };
    const nextMessages = [...messages, userMessage, assistantMessage];

    setInput('');
    setIsLoading(true);
    setMessages(nextMessages);

    const history = [...messages, userMessage]
      .slice(-6)
      .map((message) => ({
        role: message.role === 'assistant' ? 'assistant' : 'user',
        content: message.content,
      }));

    try {
      const response = await chatWithContract(auditId, query, history);
      if (!response.body) throw new Error('Streaming response is not available.');

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let accumulated = '';
      let done = false;

      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        accumulated += decoder.decode(value || new Uint8Array(), { stream: !done });
        updateAssistantMessage(assistantMessage.id, parseStreamPayload(accumulated));
      }
    } catch (err) {
      updateAssistantMessage(assistantMessage.id, {
        content: `Failed to retrieve answer. ${err.message || 'Unknown network error.'}`,
        confidence: 'NOT_FOUND',
        citations: [],
      });
    } finally {
      setIsLoading(false);
    }
  };

  const toggleCitations = (id) => {
    setOpenCitations((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <Drawer open={isOpen} onClose={onClose} title="Contract Q&A" width="w-[400px]" hideHeader={true}>

      {/* ── Header ── */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 bg-white flex-shrink-0">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="rounded-lg bg-teal-600 p-1.5 text-white flex-shrink-0">
            <Bot className="h-4 w-4 stroke-[1.5]" />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium text-slate-900 leading-none">Contract Q&A</p>
            <p className="text-xs text-slate-400 mt-0.5 truncate">
              {supplierName || 'General Contract'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {messages.length > 0 && (
            <button
              type="button"
              onClick={() => { setMessages([]); setOpenCitations({}); }}
              className="text-xs text-slate-400 hover:text-slate-600 transition-colors px-2 py-1 rounded-md hover:bg-slate-50"
            >
              Clear
            </button>
          )}
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors border border-transparent hover:border-slate-200"
            aria-label="Close panel"
          >
            <X className="h-5 w-5 stroke-[1.5]" />
          </button>
        </div>
      </div>

      {/* ── Body ── */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 scroll-smooth [scrollbar-width:thin] [scrollbar-color:theme(colors.slate.200)_transparent]">

        {messages.length === 0 ? (
          /* Empty state */
          <div className="flex h-full flex-col items-center justify-center gap-5 px-2 pb-4">
            <div className="text-center">
              <div className="inline-flex items-center justify-center h-12 w-12 rounded-2xl bg-teal-50 border border-teal-200/50 mb-3">
                <Sparkles className="h-5 w-5 text-teal-600 stroke-[1.5]" />
              </div>
              <h4 className="text-sm font-semibold text-slate-900">Ask the contract</h4>
              <p className="text-xs text-slate-400 mt-1 max-w-[220px] mx-auto leading-relaxed">
                Instant answers grounded in the extracted legal text.
              </p>
            </div>

            <div className="w-full space-y-2">
              {suggestedQuestions.map((question) => (
                <button
                  key={question}
                  type="button"
                  onClick={() => handleSend(question)}
                  className="group flex w-full items-center gap-3 rounded-xl border border-slate-200 bg-white px-3.5 py-3 text-left text-xs text-slate-600 transition-all duration-200 hover:border-teal-300 hover:bg-teal-50/40 hover:text-slate-900"
                >
                  <div className="h-5 w-5 rounded-full bg-slate-100 flex items-center justify-center group-hover:bg-teal-100 transition-colors shrink-0">
                    <ChevronRight className="h-3 w-3 text-slate-400 group-hover:text-teal-600 transition-colors stroke-[1.5]" />
                  </div>
                  {question}
                </button>
              ))}
            </div>
          </div>
        ) : (
          /* Messages */
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex flex-col ${message.role === 'user' ? 'items-end' : 'items-start'}`}
            >
              {/* Bubble */}
              <div
                className={`max-w-[84%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed ${message.role === 'user'
                  ? 'bg-teal-600 text-white rounded-br-sm'
                  : 'bg-slate-50 border border-slate-200 text-slate-800 rounded-bl-sm'
                  }`}
              >
                {message.role === 'assistant' && !message.content && isLoading ? (
                  <span className="inline-flex items-center gap-1 py-0.5">
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-300" />
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-300 [animation-delay:150ms]" />
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-300 [animation-delay:300ms]" />
                  </span>
                ) : (
                  <div className="whitespace-pre-line">{message.content}</div>
                )}
              </div>

              {/* Meta row: clause refs + confidence */}
              {message.role === 'assistant' && (message.citations?.length > 0 || message.confidence) && (
                <div className="flex items-center gap-2 mt-1.5 px-1 max-w-[84%]">
                  {message.citations?.length > 0 && (
                    <span className="flex items-center gap-1 text-[11px] text-slate-400">
                      <FileText className="h-3 w-3 text-teal-500 shrink-0 stroke-[1.5]" />
                      <span className="truncate">{message.citations.map((c) => c.clause_reference).join(', ')}</span>
                    </span>
                  )}
                  {message.citations?.length > 0 && message.confidence && (
                    <span className="text-slate-200">·</span>
                  )}
                  {message.confidence && (
                    <span className="flex items-center gap-1 text-[11px] text-slate-400">
                      <span className={`h-1.5 w-1.5 rounded-full shrink-0 ${confidenceDotClass(message.confidence)}`} />
                      {confidenceLabel(message.confidence)}
                    </span>
                  )}
                </div>
              )}

              {/* Clause toggle */}
              {message.role === 'assistant' && message.citations?.length > 0 && (
                <div className="w-full max-w-[84%] mt-1 pl-0.5">
                  <button
                    type="button"
                    onClick={() => toggleCitations(message.id)}
                    className="flex items-center gap-1 text-[11px] font-medium text-teal-600 hover:text-teal-700 px-1.5 py-0.5 rounded transition-colors hover:bg-teal-50"
                  >
                    <ChevronRight
                      className={`h-3 w-3 transition-transform duration-200 stroke-[1.5] ${openCitations[message.id] ? 'rotate-90' : ''}`}
                    />
                    {openCitations[message.id] ? 'Hide' : 'Show'} clause text
                  </button>

                  {openCitations[message.id] && (
                    <div className="mt-1.5 rounded-xl border border-slate-200 bg-white p-3 space-y-2.5 text-xs animate-in fade-in slide-in-from-top-1 duration-150">
                      {message.citations.map((cite, index) => (
                        <div
                          key={`${cite.clause_reference}-${index}`}
                          className="border-b border-slate-100 pb-2.5 last:border-0 last:pb-0"
                        >
                          <p className="font-semibold text-slate-800 mb-1">{cite.clause_reference}</p>
                          {cite.clause_text && (
                            <p className="text-slate-500 leading-relaxed italic border-l-2 border-slate-200 pl-2">
                              {cite.clause_text}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))
        )}
        <div ref={chatEndRef} />
      </div>

      {/* ── Input ── */}
      <div className="border-t border-slate-100 bg-white p-3 flex-shrink-0">
        <div className="flex items-end gap-2 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 transition-all focus-within:border-teal-400 focus-within:ring-2 focus-within:ring-teal-500/10">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
            placeholder="Ask about pricing, terms…"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            rows={1}
            className="flex-1 resize-none bg-transparent outline-none text-sm text-slate-700 placeholder:text-slate-400 disabled:opacity-50 leading-relaxed py-1 max-h-24"
          />
          <button
            type="button"
            onClick={() => handleSend()}
            disabled={isLoading || !input.trim()}
            aria-label="Send contract question"
            className="flex-shrink-0 h-8 w-8 flex items-center justify-center rounded-lg bg-teal-600 text-white transition-all duration-150 disabled:bg-slate-200 disabled:text-slate-400 disabled:cursor-not-allowed hover:bg-teal-700 active:scale-95 mb-0.5"
          >
            {isLoading
              ? <Loader2 className="h-3.5 w-3.5 animate-spin" />
              : <Send className="h-3.5 w-3.5 stroke-[1.5]" />
            }
          </button>
        </div>
      </div>

    </Drawer>
  );
}