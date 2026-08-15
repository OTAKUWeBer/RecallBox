import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { SearchBar } from './components/SearchBar';
import { MemoryCard } from './components/MemoryCard';
import { MemoryDetailModal } from './components/MemoryDetailModal';
import { WhySavedModal } from './components/WhySavedModal';
import { GraphView } from './components/GraphView';
import { RemindersView } from './components/RemindersView';
import { DigestView } from './components/DigestView';
import { PrivacyCenter } from './components/PrivacyCenter';
import { CommandPalette } from './components/CommandPalette';
import { QuickCaptureModal } from './components/QuickCaptureModal';
import { api } from './lib/api';
import { Memory, SearchResultItem } from './lib/types';
import { Inbox, Brain, Sparkles, Filter, SlidersHorizontal, RefreshCw } from 'lucide-react';

export const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<string>('inbox');
  const [sourceTypeFilter, setSourceTypeFilter] = useState<string | undefined>();
  const [memories, setMemories] = useState<Memory[]>([]);
  const [searchResults, setSearchResults] = useState<SearchResultItem[] | null>(null);
  const [searchConfidence, setSearchConfidence] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchLoading, setSearchLoading] = useState<boolean>(false);

  // Modals state
  const [selectedMemory, setSelectedMemory] = useState<Memory | null>(null);
  const [inspectingWhyMemory, setInspectingWhyMemory] = useState<Memory | null>(null);
  const [isQuickCaptureOpen, setIsQuickCaptureOpen] = useState<boolean>(false);
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState<boolean>(false);

  // Active Tag Filter
  const [selectedTag, setSelectedTag] = useState<string | undefined>();

  // Fetch memories based on view and filters
  const loadMemories = async () => {
    setLoading(true);
    try {
      const statusParam = currentView === 'inbox' ? 'inbox' : undefined;
      const data = await api.getMemories({
        status: statusParam,
        source_type: sourceTypeFilter,
        tag: selectedTag
      });
      setMemories(data);
    } catch (e) {
      console.error('Failed to load memories:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (currentView === 'inbox' || currentView === 'memories') {
      loadMemories();
    }
  }, [currentView, sourceTypeFilter, selectedTag]);

  // Global Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Command Palette: Cmd+K or Ctrl+K
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setIsCommandPaletteOpen(prev => !prev);
      }
      // Quick capture: 'c' when not inside an input/textarea
      if (e.key === 'c' && !['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement)?.tagName)) {
        e.preventDefault();
        setIsQuickCaptureOpen(true);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Hybrid Search handler
  const handleSearch = async (query: string) => {
    if (!query.trim()) {
      setSearchResults(null);
      setSearchConfidence(null);
      return;
    }
    setSearchLoading(true);
    try {
      const res = await api.search(query.trim(), selectedTag, sourceTypeFilter);
      setSearchResults(res.results);
      setSearchConfidence(res.confidence_statement || null);
    } catch (e) {
      console.error('Search failed:', e);
    } finally {
      setSearchLoading(false);
    }
  };

  // Memory Actions
  const handleToggleFavorite = async (memory: Memory, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const updated = await api.updateMemory(memory.id, { is_favorite: !memory.is_favorite });
      setMemories(prev => prev.map(m => m.id === memory.id ? updated : m));
      if (selectedMemory?.id === memory.id) setSelectedMemory(updated);
    } catch (e) {
      console.error(e);
    }
  };

  const handleArchive = async (memory: Memory, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const updated = await api.updateMemory(memory.id, {
        status: memory.status === 'archived' ? 'active' : 'archived'
      });
      setMemories(prev => prev.map(m => m.id === memory.id ? updated : m));
      if (selectedMemory?.id === memory.id) setSelectedMemory(updated);
      if (currentView === 'inbox') {
        setMemories(prev => prev.filter(m => m.id !== memory.id));
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleDelete = async (memory: Memory, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm(`Permanently delete "${memory.title}"?`)) {
      try {
        await api.deleteMemory(memory.id);
        setMemories(prev => prev.filter(m => m.id !== memory.id));
        if (selectedMemory?.id === memory.id) setSelectedMemory(null);
      } catch (e) {
        console.error(e);
      }
    }
  };

  const handleUpdateMemory = async (id: string, updates: Partial<Memory>) => {
    try {
      const updated = await api.updateMemory(id, updates);
      setMemories(prev => prev.map(m => m.id === id ? updated : m));
      if (selectedMemory?.id === id) setSelectedMemory(updated);
    } catch (e) {
      console.error(e);
    }
  };

  const inboxCount = memories.filter(m => m.status === 'inbox').length;

  return (
    <div className="flex h-screen bg-[#090d16] text-slate-100 overflow-hidden font-sans">
      {/* Sidebar */}
      <Sidebar
        currentView={currentView}
        onSelectView={(v) => {
          setCurrentView(v);
          setSearchResults(null);
        }}
        selectedSourceType={sourceTypeFilter}
        onSelectSourceType={setSourceTypeFilter}
        onOpenQuickCapture={() => setIsQuickCaptureOpen(true)}
        inboxCount={inboxCount}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Top Omni-Search Header */}
        <header className="px-6 py-3.5 border-b border-slate-800/80 bg-[#0c101d] flex items-center justify-between gap-4 z-10">
          <SearchBar
            onSearch={handleSearch}
            onOpenCommandPalette={() => setIsCommandPaletteOpen(true)}
            isLoading={searchLoading}
          />
        </header>

        {/* View Content Renderer */}
        <main className="flex-1 overflow-y-auto flex flex-col">
          {searchResults !== null ? (
            /* Search Results View */
            <div className="p-6 space-y-4 max-w-6xl mx-auto w-full">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-sky-400" />
                    Hybrid Search Results ({searchResults.length})
                  </h2>
                  {searchConfidence && (
                    <p className="text-xs text-sky-400/80 mt-0.5 font-mono">{searchConfidence}</p>
                  )}
                </div>
                <button
                  onClick={() => setSearchResults(null)}
                  className="text-xs text-slate-400 hover:text-slate-200"
                >
                  Clear Search
                </button>
              </div>

              {searchResults.length === 0 ? (
                <div className="py-16 text-center text-slate-400 text-xs">
                  No memories found matching your query.
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {searchResults.map(item => (
                    <MemoryCard
                      key={item.memory.id}
                      memory={item.memory}
                      searchScore={item.score}
                      searchHighlights={item.matched_highlights}
                      onSelect={(m) => setSelectedMemory(m)}
                      onInspectWhy={(m, e) => {
                        e.stopPropagation();
                        setInspectingWhyMemory(m);
                      }}
                      onToggleFavorite={handleToggleFavorite}
                      onArchive={handleArchive}
                      onDelete={handleDelete}
                    />
                  ))}
                </div>
              )}
            </div>
          ) : currentView === 'inbox' ? (
            /* Inbox View (Triage) */
            <div className="p-6 space-y-4 max-w-6xl mx-auto w-full flex-1">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                    <Inbox className="w-4 h-4 text-sky-400" />
                    Inbox (Triage)
                  </h2>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Newly captured items waiting for your review. Archive, tag, or set a reminder.
                  </p>
                </div>
                <button
                  onClick={loadMemories}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
                  title="Refresh Inbox"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                </button>
              </div>

              {loading ? (
                <div className="py-16 text-center text-slate-400 text-xs">Loading inbox captures...</div>
              ) : memories.length === 0 ? (
                <div className="py-20 text-center text-slate-400 space-y-2 max-w-md mx-auto">
                  <div className="w-10 h-10 rounded-full bg-slate-900 flex items-center justify-center mx-auto text-sky-400 border border-slate-800">
                    <Inbox className="w-5 h-5" />
                  </div>
                  <h3 className="text-sm font-semibold text-slate-200">Inbox Zero!</h3>
                  <p className="text-xs text-slate-400">
                    All caught up. Use the browser extension or click "Remember Something" to capture interesting pages, repos, or decisions.
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {memories.map(mem => (
                    <MemoryCard
                      key={mem.id}
                      memory={mem}
                      onSelect={(m) => setSelectedMemory(m)}
                      onInspectWhy={(m, e) => {
                        e.stopPropagation();
                        setInspectingWhyMemory(m);
                      }}
                      onToggleFavorite={handleToggleFavorite}
                      onArchive={handleArchive}
                      onDelete={handleDelete}
                    />
                  ))}
                </div>
              )}
            </div>
          ) : currentView === 'memories' ? (
            /* Memories All View */
            <div className="p-6 space-y-4 max-w-6xl mx-auto w-full flex-1">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                    <Brain className="w-4 h-4 text-sky-400" />
                    All Memories ({memories.length})
                  </h2>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Your complete local-first knowledge vault.
                  </p>
                </div>
              </div>

              {loading ? (
                <div className="py-16 text-center text-slate-400 text-xs">Loading memories...</div>
              ) : memories.length === 0 ? (
                <div className="py-16 text-center text-slate-400 text-xs">No memories found.</div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {memories.map(mem => (
                    <MemoryCard
                      key={mem.id}
                      memory={mem}
                      onSelect={(m) => setSelectedMemory(m)}
                      onInspectWhy={(m, e) => {
                        e.stopPropagation();
                        setInspectingWhyMemory(m);
                      }}
                      onToggleFavorite={handleToggleFavorite}
                      onArchive={handleArchive}
                      onDelete={handleDelete}
                    />
                  ))}
                </div>
              )}
            </div>
          ) : currentView === 'graph' ? (
            <GraphView
              onSelectMemory={async (id) => {
                const mem = await api.getMemory(id);
                setSelectedMemory(mem);
              }}
            />
          ) : currentView === 'reminders' ? (
            <RemindersView
              onSelectMemory={async (id) => {
                const mem = await api.getMemory(id);
                setSelectedMemory(mem);
              }}
            />
          ) : currentView === 'digest' ? (
            <DigestView
              onSelectMemory={async (id) => {
                const mem = await api.getMemory(id);
                setSelectedMemory(mem);
              }}
            />
          ) : currentView === 'privacy' ? (
            <PrivacyCenter />
          ) : null}
        </main>
      </div>

      {/* Modals */}
      {selectedMemory && (
        <MemoryDetailModal
          memory={selectedMemory}
          onClose={() => setSelectedMemory(null)}
          onUpdate={handleUpdateMemory}
          onDelete={async (id) => {
            await api.deleteMemory(id);
            setMemories(prev => prev.filter(m => m.id !== id));
            setSelectedMemory(null);
          }}
          onInspectWhy={(m) => {
            setInspectingWhyMemory(m);
          }}
        />
      )}

      {inspectingWhyMemory && (
        <WhySavedModal
          memory={inspectingWhyMemory}
          onClose={() => setInspectingWhyMemory(null)}
          onSelectRelatedMemory={async (id) => {
            const mem = await api.getMemory(id);
            setInspectingWhyMemory(null);
            setSelectedMemory(mem);
          }}
        />
      )}

      <QuickCaptureModal
        isOpen={isQuickCaptureOpen}
        onClose={() => setIsQuickCaptureOpen(false)}
        onMemoryCreated={(m) => {
          setMemories(prev => [m, ...prev]);
          if (currentView !== 'inbox' && currentView !== 'memories') {
            setCurrentView('inbox');
          }
        }}
      />

      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
        onSelectView={(v) => {
          setCurrentView(v);
          setSearchResults(null);
        }}
        onOpenQuickCapture={() => setIsQuickCaptureOpen(true)}
        onSelectMemory={async (id) => {
          const mem = await api.getMemory(id);
          setSelectedMemory(mem);
        }}
      />
    </div>
  );
};
export default App;
