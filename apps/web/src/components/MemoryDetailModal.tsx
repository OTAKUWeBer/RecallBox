import React, { useState } from 'react';
import {
  X, ExternalLink, HelpCircle, Star, Trash2, Archive,
  Tag as TagIcon, Calendar, Clock, Globe, Github, Video,
  FileText, Quote, Check, Plus, Bell, Sparkles, Edit3
} from 'lucide-react';
import { Memory } from '../lib/types';

interface MemoryDetailModalProps {
  memory: Memory;
  onClose: () => void;
  onUpdate: (id: string, updates: Partial<Memory>) => void;
  onDelete: (id: string) => void;
  onInspectWhy: (memory: Memory) => void;
}

export const MemoryDetailModal: React.FC<MemoryDetailModalProps> = ({
  memory,
  onClose,
  onUpdate,
  onDelete,
  onInspectWhy
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedTitle, setEditedTitle] = useState(memory.title);
  const [editedWhy, setEditedWhy] = useState(memory.user_why || '');
  const [editedContent, setEditedContent] = useState(memory.content);
  const [newTag, setNewTag] = useState('');

  const handleSaveEdit = () => {
    onUpdate(memory.id, {
      title: editedTitle,
      user_why: editedWhy,
      content: editedContent
    });
    setIsEditing(false);
  };

  const handleAddTag = (e: React.FormEvent) => {
    e.preventDefault();
    if (newTag.trim() && !memory.tags.includes(newTag.trim().toLowerCase())) {
      const updated = [...memory.tags, newTag.trim().toLowerCase()];
      onUpdate(memory.id, { tags: updated });
      setNewTag('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    const updated = memory.tags.filter(t => t !== tagToRemove);
    onUpdate(memory.id, { tags: updated });
  };

  return (
    <div className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#0e1424] border border-slate-700/80 w-full max-w-3xl rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh] animate-fade-in">
        {/* Header Bar */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-[#0a0e19]">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-sky-400 border border-slate-700">
              {memory.source_type.toUpperCase()}
            </span>
            <span className="text-xs text-slate-400">
              Saved {new Date(memory.captured_at).toLocaleDateString()}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => onInspectWhy(memory)}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-amber-950/50 hover:bg-amber-900/60 text-amber-300 border border-amber-800/60 text-xs font-medium transition-colors"
            >
              <HelpCircle className="w-3.5 h-3.5" />
              <span>Why Did I Save This?</span>
            </button>

            <button
              onClick={() => onUpdate(memory.id, { is_favorite: !memory.is_favorite })}
              className={`p-1.5 rounded-lg hover:bg-slate-800 transition-colors ${
                memory.is_favorite ? 'text-amber-400' : 'text-slate-400'
              }`}
              title="Star"
            >
              <Star className="w-4 h-4 fill-current" />
            </button>

            <button
              onClick={() => onUpdate(memory.id, { status: memory.status === 'archived' ? 'active' : 'archived' })}
              className={`p-1.5 rounded-lg hover:bg-slate-800 transition-colors ${
                memory.status === 'archived' ? 'text-sky-400' : 'text-slate-400'
              }`}
              title="Archive"
            >
              <Archive className="w-4 h-4" />
            </button>

            <button
              onClick={() => {
                if (confirm('Permanently delete this memory?')) {
                  onDelete(memory.id);
                  onClose();
                }
              }}
              className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-slate-800 transition-colors"
              title="Delete"
            >
              <Trash2 className="w-4 h-4" />
            </button>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors ml-2"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-5 flex-1">
          {/* Title Area */}
          <div>
            {isEditing ? (
              <input
                type="text"
                value={editedTitle}
                onChange={(e) => setEditedTitle(e.target.value)}
                className="w-full text-lg font-bold bg-slate-900 border border-slate-700 rounded p-2 text-white"
              />
            ) : (
              <h2 className="text-xl font-bold text-slate-100 leading-snug">
                {memory.title}
              </h2>
            )}

            {memory.source_url && (
              <div className="mt-1.5 flex items-center gap-1.5 text-xs text-sky-400 truncate">
                <ExternalLink className="w-3.5 h-3.5 flex-shrink-0" />
                <a
                  href={memory.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:underline truncate"
                >
                  {memory.source_url}
                </a>
              </div>
            )}
          </div>

          {/* User Intention "Why" Box */}
          <div className="p-3 rounded-lg bg-amber-950/20 border border-amber-900/30">
            <div className="text-[11px] font-semibold text-amber-400 uppercase tracking-wider mb-1 flex items-center gap-1">
              <Sparkles className="w-3 h-3" />
              Capture Intent / Why You Saved This
            </div>
            {isEditing ? (
              <textarea
                value={editedWhy}
                onChange={(e) => setEditedWhy(e.target.value)}
                rows={2}
                placeholder="e.g. Try this for the upcoming microservice migration..."
                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-xs text-amber-100"
              />
            ) : (
              <p className="text-xs text-amber-200/90 italic">
                {memory.user_why || 'No specific intention note recorded during capture.'}
              </p>
            )}
          </div>

          {/* Summary Box */}
          {memory.summary && (
            <div className="p-3.5 rounded-lg bg-slate-900/90 border border-slate-800">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                AI / Extractive Summary
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                {memory.summary}
              </p>
            </div>
          )}

          {/* Extracted Topics & Possible Actions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {memory.topics.length > 0 && (
              <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800/80">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1.5">
                  Detected Topics
                </span>
                <div className="flex flex-wrap gap-1">
                  {memory.topics.map((t, idx) => (
                    <span key={idx} className="text-[11px] font-mono px-2 py-0.5 rounded bg-sky-950 text-sky-300 border border-sky-900/50">
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {memory.possible_actions.length > 0 && (
              <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800/80">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1.5">
                  Suggested Actions
                </span>
                <div className="flex flex-wrap gap-1">
                  {memory.possible_actions.map((act, idx) => (
                    <span key={idx} className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-900/50">
                      ⚡ {act}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Full Extracted Content */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Full Content / Notes
              </span>
              <button
                onClick={() => setIsEditing(!isEditing)}
                className="text-xs text-sky-400 hover:text-sky-300 flex items-center gap-1"
              >
                <Edit3 className="w-3 h-3" />
                {isEditing ? 'Cancel Edit' : 'Edit'}
              </button>
            </div>

            {isEditing ? (
              <textarea
                value={editedContent}
                onChange={(e) => setEditedContent(e.target.value)}
                rows={8}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-xs font-mono text-slate-200"
              />
            ) : (
              <div className="p-4 rounded-lg bg-slate-950 border border-slate-800/80 text-xs text-slate-300 leading-relaxed font-mono whitespace-pre-wrap max-h-64 overflow-y-auto">
                {memory.content || 'No extracted text body.'}
              </div>
            )}
          </div>

          {/* Tags Manager */}
          <div>
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">
              Tags
            </span>
            <div className="flex flex-wrap items-center gap-1.5">
              {memory.tags.map((t) => (
                <span
                  key={t}
                  className="flex items-center gap-1 text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-200 border border-slate-700"
                >
                  #{t}
                  <button
                    onClick={() => handleRemoveTag(t)}
                    className="text-slate-400 hover:text-red-400"
                  >
                    ×
                  </button>
                </span>
              ))}

              <form onSubmit={handleAddTag} className="inline-flex items-center">
                <input
                  type="text"
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  placeholder="+ add tag..."
                  className="bg-slate-900 border border-slate-800 rounded px-2 py-0.5 text-xs text-slate-300 placeholder-slate-400 focus:outline-none focus:border-sky-500"
                />
              </form>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 bg-[#0a0e19] border-t border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span>Status:</span>
            <select
              value={memory.status}
              onChange={(e) => onUpdate(memory.id, { status: e.target.value as any })}
              className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200 focus:outline-none"
            >
              <option value="inbox">Inbox</option>
              <option value="unread">Unread</option>
              <option value="active">Active</option>
              <option value="review">Review</option>
              <option value="done">Done</option>
              <option value="archived">Archived</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            {isEditing && (
              <button
                onClick={handleSaveEdit}
                className="px-4 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium transition-colors"
              >
                Save Changes
              </button>
            )}
            <button
              onClick={onClose}
              className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
