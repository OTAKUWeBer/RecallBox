import React, { useEffect, useState } from 'react';
import { Bell, CheckCircle2, Clock, Calendar, ArrowRight, Check, Sparkles, ExternalLink } from 'lucide-react';
import { api } from '../lib/api';
import { Reminder, Memory } from '../lib/types';

interface RemindersViewProps {
  onSelectMemory: (id: string) => void;
}

export const RemindersView: React.FC<RemindersViewProps> = ({ onSelectMemory }) => {
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [pendingActions, setPendingActions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const [rems, digest] = await Promise.all([
        api.getReminders(),
        api.getWeeklyDigest()
      ]);
      setReminders(rems);
      setPendingActions(digest.pending_actions || []);
    } catch (e) {
      console.error('Failed to load reminders:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleComplete = async (id: string) => {
    try {
      await api.completeReminder(id);
      loadData();
    } catch (e) {
      console.error('Failed to complete reminder:', e);
    }
  };

  const activeReminders = reminders.filter(r => !r.is_completed);
  const completedReminders = reminders.filter(r => r.is_completed);

  return (
    <div className="flex-1 p-6 space-y-6 overflow-y-auto max-w-5xl mx-auto w-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Bell className="w-5 h-5 text-sky-400" />
            Reminders & Action Items
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Never forget the things you decided you wanted to try, read, or benchmark.
          </p>
        </div>
      </div>

      {loading ? (
        <div className="py-16 text-center text-slate-400 text-xs">
          Loading scheduled reminders...
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Column 1: Scheduled Time Reminders */}
          <div className="space-y-3">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-sky-400" />
              Scheduled Time Reminders ({activeReminders.length})
            </h3>

            {activeReminders.length === 0 ? (
              <div className="p-6 rounded-xl bg-slate-900/40 border border-slate-800 text-center text-xs text-slate-400">
                No active time reminders. You can set reminders when capturing with the extension or CLI!
              </div>
            ) : (
              activeReminders.map(rem => (
                <div
                  key={rem.id}
                  className="p-4 rounded-xl bg-[#0e1424] border border-slate-800 hover:border-slate-700 space-y-2.5 transition-all shadow-sm"
                >
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <span className="flex items-center gap-1 text-amber-400 font-mono text-[11px]">
                      <Clock className="w-3.5 h-3.5" />
                      Due: {new Date(rem.remind_at).toLocaleDateString()}
                    </span>
                  </div>

                  <h4
                    onClick={() => onSelectMemory(rem.memory_id)}
                    className="font-medium text-sm text-slate-100 hover:text-sky-300 cursor-pointer"
                  >
                    {rem.memory_title || 'Memory item'}
                  </h4>

                  {rem.note && (
                    <p className="text-xs text-slate-300 italic bg-slate-900/80 p-2 rounded border border-slate-800">
                      "{rem.note}"
                    </p>
                  )}

                  <div className="pt-2 flex items-center justify-between">
                    <button
                      onClick={() => onSelectMemory(rem.memory_id)}
                      className="text-xs text-sky-400 hover:underline flex items-center gap-1"
                    >
                      <span>Open Memory</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>

                    <button
                      onClick={() => handleComplete(rem.id)}
                      className="flex items-center gap-1 text-xs px-2.5 py-1 rounded bg-emerald-950/60 hover:bg-emerald-900/80 text-emerald-300 border border-emerald-800/60 font-medium transition-colors"
                    >
                      <Check className="w-3 h-3" />
                      <span>Done</span>
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Column 2: Contextual Action Opportunities */}
          <div className="space-y-3">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              Detected Action Opportunities ({pendingActions.length})
            </h3>

            {pendingActions.length === 0 ? (
              <div className="p-6 rounded-xl bg-slate-900/40 border border-slate-800 text-center text-xs text-slate-400">
                No pending actionable memories found.
              </div>
            ) : (
              pendingActions.map((act, idx) => (
                <div
                  key={idx}
                  onClick={() => onSelectMemory(act.memory_id)}
                  className="p-3.5 rounded-xl bg-[#0e1424] border border-slate-800 hover:border-slate-700 cursor-pointer space-y-2 transition-all group"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950/80 text-amber-300 border border-amber-800/40">
                      ⚡ Action: {act.action}
                    </span>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-sky-400 transition-colors" />
                  </div>
                  <h4 className="text-xs font-medium text-slate-200 group-hover:text-sky-300 leading-snug">
                    {act.title}
                  </h4>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};
