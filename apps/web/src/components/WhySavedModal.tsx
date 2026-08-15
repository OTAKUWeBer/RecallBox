import React, { useEffect, useState } from 'react';
import { HelpCircle, Clock, Link2, Sparkles, X, ArrowRight, ShieldCheck, CheckCircle2 } from 'lucide-react';
import { api } from '../lib/api';
import { WhyDidISaveThisResponse, Memory } from '../lib/types';

interface WhySavedModalProps {
  memory: Memory;
  onClose: () => void;
  onSelectRelatedMemory: (id: string) => void;
}

export const WhySavedModal: React.FC<WhySavedModalProps> = ({
  memory,
  onClose,
  onSelectRelatedMemory
}) => {
  const [contextData, setContextData] = useState<WhyDidISaveThisResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    async function loadContext() {
      setLoading(true);
      try {
        const res = await api.getWhySavedContext(memory.id);
        if (isMounted) setContextData(res);
      } catch (err) {
        console.error('Failed to load save context:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadContext();
    return () => { isMounted = false; };
  }, [memory.id]);

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#0e1424] border border-amber-500/30 w-full max-w-xl rounded-xl shadow-2xl overflow-hidden animate-fade-in">
        {/* Header */}
        <div className="bg-amber-950/30 border-b border-amber-900/40 p-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center border border-amber-500/30">
              <HelpCircle className="w-4 h-4" />
            </div>
            <div>
              <h2 className="font-semibold text-sm text-amber-100 flex items-center gap-2">
                Why Did You Save This?
                <span className="text-[10px] font-mono uppercase px-1.5 py-0.2 rounded bg-amber-900/50 text-amber-300 border border-amber-700/50">
                  Context Reconstruction
                </span>
              </h2>
              <p className="text-xs text-amber-300/70 truncate max-w-sm">{memory.title}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-amber-400/80 hover:text-amber-200 hover:bg-amber-950/60 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 space-y-4 max-h-[75vh] overflow-y-auto">
          {loading ? (
            <div className="py-12 flex flex-col items-center justify-center text-slate-400 gap-2">
              <div className="w-6 h-6 border-2 border-amber-400/30 border-t-amber-400 rounded-full animate-spin" />
              <span className="text-xs">Reconstructing timeline & session evidence...</span>
            </div>
          ) : contextData ? (
            <>
              {/* Evidence-Backed Synthesized Context Box */}
              <div className="p-3.5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span className="flex items-center gap-1 text-slate-300 font-medium">
                    <Clock className="w-3.5 h-3.5 text-amber-400" />
                    Saved {contextData.saved_days_ago === 0 ? 'today' : `${contextData.saved_days_ago} days ago`} ({new Date(contextData.captured_at).toLocaleDateString()})
                  </span>
                  <span className="flex items-center gap-1 text-[11px] text-emerald-400 font-mono">
                    <ShieldCheck className="w-3 h-3" />
                    100% Evidence-backed (No hallucination)
                  </span>
                </div>
                <p className="text-sm text-slate-200 leading-relaxed">
                  {contextData.context_summary}
                </p>
              </div>

              {/* Explicit User Note if Present */}
              {contextData.user_explicit_why && (
                <div className="p-3 rounded-lg bg-amber-950/20 border border-amber-900/40">
                  <div className="text-[11px] font-semibold text-amber-400 uppercase tracking-wider mb-1">
                    Your Original Intention Note:
                  </div>
                  <p className="text-xs text-amber-200 italic">
                    "{contextData.user_explicit_why}"
                  </p>
                </div>
              )}

              {/* Active Research Trail Topics */}
              {contextData.active_research_trail.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                    Active Research Session Topics:
                  </h4>
                  <div className="flex flex-wrap gap-1.5">
                    {contextData.active_research_trail.map((topic, i) => (
                      <span
                        key={i}
                        className="text-xs font-mono px-2 py-0.5 rounded-md bg-slate-800/90 text-sky-300 border border-slate-700/60"
                      >
                        {topic}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Related Items Saved in the Same Time Window */}
              {contextData.related_memories_saved_around_then.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                    Related Items Saved Around The Same Time ({contextData.related_memories_saved_around_then.length}):
                  </h4>
                  <div className="space-y-2">
                    {contextData.related_memories_saved_around_then.map((item) => (
                      <div
                        key={item.memory_id}
                        onClick={() => onSelectRelatedMemory(item.memory_id)}
                        className="group flex items-center justify-between p-2.5 rounded-lg bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800 hover:border-slate-700 cursor-pointer transition-all"
                      >
                        <div className="overflow-hidden pr-3">
                          <h5 className="text-xs font-medium text-slate-200 group-hover:text-sky-300 truncate">
                            {item.title}
                          </h5>
                          <span className="text-[11px] text-slate-400 flex items-center gap-1.5 mt-0.5">
                            <span className="text-amber-400/90 font-mono text-[10px]">{item.relationship}</span>
                            {item.source_url && (
                              <span className="truncate max-w-[200px] text-slate-400">· {item.source_url}</span>
                            )}
                          </span>
                        </div>
                        <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-sky-400 transition-colors flex-shrink-0" />
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <p className="text-xs text-slate-400 text-center py-6">Could not load context details.</p>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 bg-slate-950/80 border-t border-slate-800/80 flex justify-end">
          <button
            onClick={onClose}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
