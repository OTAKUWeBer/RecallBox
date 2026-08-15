import React, { useEffect, useState } from 'react';
import { Sparkles, Calendar, TrendingUp, Archive, Flame, AlertCircle, ArrowRight, BookOpen } from 'lucide-react';
import { api } from '../lib/api';
import { WeeklyDigest, Memory } from '../lib/types';

interface DigestViewProps {
  onSelectMemory: (id: string) => void;
}

export const DigestView: React.FC<DigestViewProps> = ({ onSelectMemory }) => {
  const [digest, setDigest] = useState<WeeklyDigest | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const res = await api.getWeeklyDigest();
        setDigest(res);
      } catch (e) {
        console.error('Failed to load digest:', e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="flex-1 p-6 space-y-6 overflow-y-auto max-w-4xl mx-auto w-full">
      {/* Header */}
      <div className="border-b border-slate-800 pb-5">
        <div className="flex items-center gap-2 text-sky-400 mb-1">
          <Sparkles className="w-5 h-5" />
          <span className="text-xs font-mono uppercase tracking-widest font-semibold">Weekly Synthesis</span>
        </div>
        <h2 className="text-2xl font-bold text-slate-100 tracking-tight">Your Recall</h2>
        <p className="text-xs text-slate-400 mt-1 flex items-center gap-1.5">
          <Calendar className="w-3.5 h-3.5" />
          {digest ? `${new Date(digest.period_start).toLocaleDateString()} — ${new Date(digest.period_end).toLocaleDateString()}` : 'Past 7 Days'}
        </p>
      </div>

      {loading ? (
        <div className="py-16 text-center text-slate-400 text-xs">
          Synthesizing your memory digest...
        </div>
      ) : digest ? (
        <div className="space-y-6">
          {/* Summary Stat Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-[#0e1424] border border-slate-800">
              <span className="text-xs text-slate-400">Total Saved (7 Days)</span>
              <div className="text-2xl font-bold text-sky-400 mt-1 font-mono">{digest.total_saved}</div>
            </div>

            <div className="p-4 rounded-xl bg-[#0e1424] border border-slate-800">
              <span className="text-xs text-slate-400">Top Focus Topics</span>
              <div className="text-sm font-semibold text-slate-200 mt-1 truncate">
                {digest.top_topics.map(t => t.topic).slice(0, 3).join(', ') || 'Various'}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-[#0e1424] border border-slate-800">
              <span className="text-xs text-slate-400">Forgotten Gems Rediscovered</span>
              <div className="text-2xl font-bold text-amber-400 mt-1 font-mono">{digest.forgotten_ideas.length}</div>
            </div>
          </div>

          {/* Section: Most Interesting Saves */}
          <div className="space-y-3">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <Flame className="w-3.5 h-3.5 text-orange-400" />
              High-Signal Captures ({digest.most_interesting.length})
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {digest.most_interesting.map(m => (
                <div
                  key={m.id}
                  onClick={() => onSelectMemory(m.id)}
                  className="p-3.5 rounded-xl bg-[#0e1424] border border-slate-800 hover:border-slate-700 cursor-pointer transition-all group"
                >
                  <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
                    <span className="font-mono text-sky-400 uppercase">{m.source_type}</span>
                    <span>{new Date(m.captured_at).toLocaleDateString()}</span>
                  </div>
                  <h4 className="text-xs font-semibold text-slate-100 group-hover:text-sky-300 leading-snug line-clamp-1">
                    {m.title}
                  </h4>
                  <p className="text-xs text-slate-300 line-clamp-2 mt-1">
                    {m.summary || m.content}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Section: Forgotten Ideas (>30 days old unread) */}
          {digest.forgotten_ideas.length > 0 && (
            <div className="space-y-3 pt-2">
              <h3 className="text-xs font-semibold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
                Forgotten Ideas You Wanted To Come Back To
              </h3>
              <div className="space-y-2">
                {digest.forgotten_ideas.map(m => (
                  <div
                    key={m.id}
                    onClick={() => onSelectMemory(m.id)}
                    className="p-3.5 rounded-xl bg-amber-950/10 border border-amber-900/30 hover:border-amber-700/50 cursor-pointer transition-all flex items-center justify-between group"
                  >
                    <div className="overflow-hidden pr-3">
                      <h4 className="text-xs font-semibold text-amber-100 group-hover:text-amber-300 truncate">
                        {m.title}
                      </h4>
                      <p className="text-[11px] text-amber-200/70 italic mt-0.5 line-clamp-1">
                        {m.user_why || m.summary || 'Saved for later'}
                      </p>
                    </div>
                    <ArrowRight className="w-4 h-4 text-amber-400/70 group-hover:text-amber-300 flex-shrink-0" />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
};
