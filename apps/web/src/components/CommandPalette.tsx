import React, { useEffect, useState } from 'react';
import {
  Search, Plus, Brain, Inbox, Share2, Bell, Sparkles, Shield,
  Download, ArrowRight, X, Command
} from 'lucide-react';
import { api } from '../lib/api';
import { Memory } from '../lib/types';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectView: (view: string) => void;
  onOpenQuickCapture: () => void;
  onSelectMemory: (id: string) => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  onSelectView,
  onOpenQuickCapture,
  onSelectMemory
}) => {
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Memory[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);

  useEffect(() => {
    if (!isOpen) {
      setQuery('');
      setSearchResults([]);
      setSelectedIndex(0);
      return;
    }

    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [isOpen, onClose]);

  // Live search as user types in command palette
  useEffect(() => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const res = await api.search(query.trim());
        setSearchResults(res.results.map(r => r.memory).slice(0, 6));
      } catch (e) {
        console.error(e);
      }
    }, 150);
    return () => clearTimeout(timer);
  }, [query]);

  if (!isOpen) return null;

  const standardCommands = [
    { id: 'capture', label: 'Remember Something (Quick Capture)', icon: Plus, action: onOpenQuickCapture },
    { id: 'inbox', label: 'Go to Inbox', icon: Inbox, action: () => onSelectView('inbox') },
    { id: 'memories', label: 'Go to Memories', icon: Brain, action: () => onSelectView('memories') },
    { id: 'graph', label: 'Go to Knowledge Graph', icon: Share2, action: () => onSelectView('graph') },
    { id: 'reminders', label: 'Go to Reminders', icon: Bell, action: () => onSelectView('reminders') },
    { id: 'digest', label: 'Go to Your Recall Digest', icon: Sparkles, action: () => onSelectView('digest') },
    { id: 'privacy', label: 'Go to Privacy & Storage', icon: Shield, action: () => onSelectView('privacy') },
  ];

  return (
    <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-start justify-center pt-20 p-4">
      <div className="bg-[#0e1424] border border-slate-700/80 w-full max-w-xl rounded-xl shadow-2xl overflow-hidden animate-fade-in">
        {/* Search Input in Palette */}
        <div className="relative border-b border-slate-800 p-3 flex items-center gap-2.5">
          <Search className="w-4 h-4 text-slate-400" />
          <input
            autoFocus
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command or search memory..."
            className="w-full bg-transparent text-sm text-slate-100 placeholder-slate-400 focus:outline-none"
          />
          <kbd className="text-[10px] font-mono bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded border border-slate-700">ESC</kbd>
        </div>

        {/* Results List */}
        <div className="p-2 max-h-80 overflow-y-auto space-y-1">
          {searchResults.length > 0 && (
            <div className="pb-1">
              <div className="px-2 py-1 text-[10px] font-mono uppercase text-slate-400 tracking-wider">
                Matching Memories
              </div>
              {searchResults.map((m) => (
                <div
                  key={m.id}
                  onClick={() => {
                    onSelectMemory(m.id);
                    onClose();
                  }}
                  className="flex items-center justify-between px-3 py-2 rounded-lg hover:bg-slate-800/80 cursor-pointer text-xs group"
                >
                  <div className="flex items-center gap-2 overflow-hidden">
                    <span className="text-[10px] font-mono text-sky-400 uppercase bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">
                      {m.source_type}
                    </span>
                    <span className="text-slate-200 group-hover:text-sky-300 truncate">
                      {m.title}
                    </span>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-sky-400" />
                </div>
              ))}
            </div>
          )}

          <div>
            <div className="px-2 py-1 text-[10px] font-mono uppercase text-slate-400 tracking-wider">
              Navigation & Actions
            </div>
            {standardCommands.map((cmd) => {
              const Icon = cmd.icon;
              return (
                <div
                  key={cmd.id}
                  onClick={() => {
                    cmd.action();
                    onClose();
                  }}
                  className="flex items-center justify-between px-3 py-2 rounded-lg hover:bg-slate-800/80 cursor-pointer text-xs group text-slate-300 hover:text-slate-100"
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className="w-4 h-4 text-slate-400 group-hover:text-sky-400" />
                    <span>{cmd.label}</span>
                  </div>
                  <kbd className="text-[10px] font-mono text-slate-400 bg-slate-900 px-1 py-0.5 rounded border border-slate-800">↵</kbd>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
