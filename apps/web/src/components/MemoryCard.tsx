import React from 'react';
import {
  Github, Globe, Video, FileText, Quote, Star, Archive,
  Trash2, HelpCircle, ExternalLink, Clock, Tag as TagIcon, Bell
} from 'lucide-react';
import { Memory } from '../lib/types';
import { SafeHighlight } from './SafeHighlight';

interface MemoryCardProps {
  memory: Memory;
  onSelect: (memory: Memory) => void;
  onInspectWhy: (memory: Memory, e: React.MouseEvent) => void;
  onToggleFavorite: (memory: Memory, e: React.MouseEvent) => void;
  onArchive: (memory: Memory, e: React.MouseEvent) => void;
  onDelete: (memory: Memory, e: React.MouseEvent) => void;
  searchScore?: number;
  searchHighlights?: string[];
}

export const MemoryCard: React.FC<MemoryCardProps> = ({
  memory,
  onSelect,
  onInspectWhy,
  onToggleFavorite,
  onArchive,
  onDelete,
  searchScore,
  searchHighlights
}) => {
  const getSourceIcon = () => {
    switch (memory.source_type) {
      case 'repository': return <Github className="w-3.5 h-3.5 text-purple-400" />;
      case 'video': return <Video className="w-3.5 h-3.5 text-red-400" />;
      case 'note': return <FileText className="w-3.5 h-3.5 text-amber-400" />;
      case 'quote': return <Quote className="w-3.5 h-3.5 text-emerald-400" />;
      default: return <Globe className="w-3.5 h-3.5 text-sky-400" />;
    }
  };

  const timeAgo = (dateStr: string) => {
    try {
      const now = new Date();
      const past = new Date(dateStr);
      const diffSec = Math.max(Math.floor((now.getTime() - past.getTime()) / 1000), 0);
      if (diffSec < 60) return 'Just now';
      if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
      if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
      const days = Math.floor(diffSec / 86400);
      if (days === 1) return 'Yesterday';
      return `${days}d ago`;
    } catch {
      return '';
    }
  };

  return (
    <div
      onClick={() => onSelect(memory)}
      className="group relative bg-[#0e1424] hover:bg-[#131b31] border border-slate-800/80 hover:border-slate-700/80 rounded-xl p-4 transition-all duration-150 cursor-pointer shadow-sm hover:shadow-md flex flex-col justify-between"
    >
      <div>
        {/* Header Metadata */}
        <div className="flex items-center justify-between gap-2 mb-2">
          <div className="flex items-center gap-2 overflow-hidden">
            <span className="p-1 rounded bg-slate-800/80 border border-slate-700/50 flex-shrink-0">
              {getSourceIcon()}
            </span>
            <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider font-mono truncate">
              {memory.source_type}
            </span>
            {searchScore !== undefined && (
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-sky-950/80 text-sky-300 border border-sky-800/40 flex-shrink-0">
                {Math.round(searchScore * 100)}% match
              </span>
            )}
          </div>

          <div className="flex items-center gap-1 opacity-80 group-hover:opacity-100 transition-opacity">
            <span className="text-[11px] text-slate-400 flex items-center gap-1 mr-1">
              <Clock className="w-3 h-3" />
              {timeAgo(memory.captured_at)}
            </span>
            <button
              onClick={(e) => onToggleFavorite(memory, e)}
              className={`p-1 rounded hover:bg-slate-800 transition-colors ${
                memory.is_favorite ? 'text-amber-400' : 'text-slate-400 hover:text-slate-200'
              }`}
              title={memory.is_favorite ? 'Starred' : 'Star memory'}
            >
              <Star className="w-3.5 h-3.5 fill-current" />
            </button>
          </div>
        </div>

        {/* Title */}
        <h3 className="font-semibold text-sm text-slate-100 group-hover:text-sky-300 transition-colors line-clamp-2 leading-snug mb-1.5">
          {memory.title}
        </h3>

        {/* User Explicit Intent ("Why did I save this?") */}
        {memory.user_why && (
          <div className="mb-2 px-2 py-1 rounded bg-amber-950/30 border border-amber-900/40 text-[11px] text-amber-200/90 flex items-start gap-1.5">
            <span className="font-semibold text-amber-400 flex-shrink-0">Why:</span>
            <span className="italic line-clamp-1">{memory.user_why}</span>
          </div>
        )}

        {/* Summary Snippet */}
        <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed mb-3">
          {memory.summary || memory.content || 'No text extracted.'}
        </p>

        {/* Highlights from Search if available */}
        {searchHighlights && searchHighlights.length > 0 && (
          <div className="mb-3 p-1.5 rounded bg-sky-950/30 border border-sky-900/30 text-[11px] text-sky-200 line-clamp-1">
            <SafeHighlight text={searchHighlights[0]} />
          </div>
        )}
      </div>

      {/* Footer Tags & Quick Actions */}
      <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 flex-wrap overflow-hidden">
          {memory.tags.slice(0, 3).map((tag, idx) => (
            <span
              key={idx}
              className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800/80 text-slate-300 border border-slate-700/50"
            >
              #{tag}
            </span>
          ))}
          {memory.tags.length > 3 && (
            <span className="text-[10px] text-slate-400 font-mono">
              +{memory.tags.length - 3}
            </span>
          )}
        </div>

        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={(e) => onInspectWhy(memory, e)}
            className="p-1 text-slate-400 hover:text-amber-300 hover:bg-slate-800 rounded transition-colors"
            title="Why did I save this? (Context trail)"
          >
            <HelpCircle className="w-3.5 h-3.5" />
          </button>

          {memory.source_url && (
            <a
              href={memory.source_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="p-1 text-slate-400 hover:text-sky-300 hover:bg-slate-800 rounded transition-colors"
              title="Open source URL"
            >
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}

          <button
            onClick={(e) => onArchive(memory, e)}
            className="p-1 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded transition-colors"
            title="Archive"
          >
            <Archive className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={(e) => onDelete(memory, e)}
            className="p-1 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded transition-colors"
            title="Delete"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
