import React, { useState } from 'react';
import { Plus, X, Globe, FileText, Sparkles, Bell } from 'lucide-react';
import { api } from '../lib/api';
import { Memory } from '../lib/types';

interface QuickCaptureModalProps {
  isOpen: boolean;
  onClose: () => void;
  onMemoryCreated: (memory: Memory) => void;
}

export const QuickCaptureModal: React.FC<QuickCaptureModalProps> = ({
  isOpen,
  onClose,
  onMemoryCreated
}) => {
  const [content, setContent] = useState('');
  const [title, setTitle] = useState('');
  const [why, setWhy] = useState('');
  const [tags, setTags] = useState('');
  const [remindMe, setRemindMe] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  if (!isOpen) return null;

  const isUrl = content.trim().startsWith('http://') || content.trim().startsWith('https://');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim() && !title.trim()) return;

    setIsSaving(true);
    try {
      const tagList = tags.split(',').map(t => t.trim()).filter(Boolean);
      let remindDate: string | undefined = undefined;
      if (remindMe) {
        const d = new Date();
        d.setDate(d.getDate() + 3);
        remindDate = d.toISOString();
      }

      const created = await api.createMemory({
        title: title.trim() || undefined,
        content: isUrl ? '' : content.trim(),
        source_url: isUrl ? content.trim() : undefined,
        user_why: why.trim() || undefined,
        tags: tagList,
        source: 'web_app',
        remind_at: remindDate
      });

      onMemoryCreated(created);
      onClose();
      setContent('');
      setTitle('');
      setWhy('');
      setTags('');
      setRemindMe(false);
    } catch (err) {
      console.error('Capture failed:', err);
      alert('Failed to save memory. Please check backend connection.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#0e1424] border border-sky-500/40 w-full max-w-lg rounded-xl shadow-2xl overflow-hidden animate-fade-in">
        {/* Header */}
        <div className="p-4 bg-sky-950/30 border-b border-sky-900/40 flex items-center justify-between">
          <div className="flex items-center gap-2 text-sky-400">
            <Sparkles className="w-4 h-4" />
            <h2 className="font-semibold text-sm text-sky-100">Remember Something</h2>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-200">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              URL or Note Content
            </label>
            <textarea
              autoFocus
              rows={3}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Paste a URL (e.g. https://github.com/...) or write down an idea, command, decision, or quote..."
              className="w-full bg-slate-900 border border-slate-700/80 rounded-lg p-3 text-xs text-slate-100 placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Title <span className="text-slate-400">(optional)</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Title for this memory (auto-extracted if URL)"
              className="w-full bg-slate-900 border border-slate-700/80 rounded-lg px-3 py-2 text-xs text-slate-100 placeholder-slate-400 focus:outline-none focus:border-sky-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-amber-300/90 mb-1">
              Why are you saving this? <span className="text-slate-400">(optional context)</span>
            </label>
            <input
              type="text"
              value={why}
              onChange={(e) => setWhy(e.target.value)}
              placeholder="e.g. Test for high-traffic telemetry, compare with Redis..."
              className="w-full bg-slate-900 border border-amber-900/40 rounded-lg px-3 py-2 text-xs text-amber-100 placeholder-slate-400 focus:outline-none focus:border-amber-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Tags <span className="text-slate-400">(comma-separated)</span>
            </label>
            <input
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="docker, prometheus, monitoring"
              className="w-full bg-slate-900 border border-slate-700/80 rounded-lg px-3 py-2 text-xs text-slate-100 placeholder-slate-400 focus:outline-none focus:border-sky-500"
            />
          </div>

          <div className="flex items-center gap-2 pt-1">
            <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={remindMe}
                onChange={(e) => setRemindMe(e.target.checked)}
                className="rounded bg-slate-900 border-slate-700 text-sky-600 focus:ring-0"
              />
              <span>Set a revisit reminder for next week</span>
            </label>
          </div>

          <div className="pt-2 border-t border-slate-800 flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold shadow-md shadow-sky-600/20 transition-all active:scale-[0.98]"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>{isSaving ? 'Remembering...' : 'Save to Memory'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
