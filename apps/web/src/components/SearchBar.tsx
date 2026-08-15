import React, { useState } from 'react';
import { Search, Sparkles, X, Command } from 'lucide-react';

interface SearchBarProps {
  onSearch: (query: string) => void;
  onOpenCommandPalette: () => void;
  isLoading?: boolean;
}

export const SearchBar: React.FC<SearchBarProps> = ({
  onSearch,
  onOpenCommandPalette,
  isLoading
}) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
    }
  };

  const handleClear = () => {
    setQuery('');
    onSearch('');
  };

  return (
    <div className="w-full flex items-center gap-3">
      <form onSubmit={handleSubmit} className="relative flex-1 group">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400 group-focus-within:text-sky-400 transition-colors">
          <Search className="w-4 h-4" />
        </div>
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            if (e.target.value === '') onSearch('');
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              handleSubmit(e);
            }
          }}
          placeholder='Ask or search your memory... (e.g. "that Docker monitoring project", "FastAPI decision")'
          className="w-full bg-slate-900/90 hover:bg-slate-900 focus:bg-slate-950 border border-slate-800 focus:border-sky-500/80 rounded-lg pl-9 pr-24 py-2 text-xs md:text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-sky-500/50 shadow-inner transition-all"
        />

        <div className="absolute inset-y-0 right-0 pr-2 flex items-center gap-1.5">
          {isLoading && (
            <div className="w-3.5 h-3.5 border-2 border-sky-400/30 border-t-sky-400 rounded-full animate-spin mr-1" />
          )}

          {query && (
            <button
              type="button"
              onClick={handleClear}
              className="text-slate-400 hover:text-slate-200 p-0.5"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}

          <button
            type="button"
            onClick={onOpenCommandPalette}
            className="flex items-center gap-0.5 text-[10px] font-mono text-slate-400 bg-slate-800/80 hover:bg-slate-700/80 px-1.5 py-0.5 rounded border border-slate-700/60 transition-colors"
          >
            <Command className="w-2.5 h-2.5" />
            <span>K</span>
          </button>
        </div>
      </form>
    </div>
  );
};
