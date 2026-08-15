import React from 'react';
import {
  Inbox,
  Brain,
  Share2,
  Bell,
  Sparkles,
  Shield,
  Plus,
  Compass,
  Github,
  Globe,
  FileText,
  Video,
  Quote,
  Star
} from 'lucide-react';

interface SidebarProps {
  currentView: string;
  onSelectView: (view: string) => void;
  selectedSourceType?: string;
  onSelectSourceType: (type: string | undefined) => void;
  onOpenQuickCapture: () => void;
  inboxCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentView,
  onSelectView,
  selectedSourceType,
  onSelectSourceType,
  onOpenQuickCapture,
  inboxCount
}) => {
  const mainNav = [
    { id: 'inbox', label: 'Inbox', icon: Inbox, count: inboxCount },
    { id: 'memories', label: 'Memories', icon: Brain },
    { id: 'graph', label: 'Knowledge Graph', icon: Share2 },
    { id: 'reminders', label: 'Reminders & Actions', icon: Bell },
    { id: 'digest', label: 'Your Recall', icon: Sparkles },
    { id: 'privacy', label: 'Privacy & Storage', icon: Shield },
  ];

  const sourceFilters = [
    { id: 'repository', label: 'GitHub', icon: Github },
    { id: 'article', label: 'Web & Articles', icon: Globe },
    { id: 'video', label: 'YouTube / Media', icon: Video },
    { id: 'note', label: 'Notes & Ideas', icon: FileText },
    { id: 'quote', label: 'Selections & Quotes', icon: Quote },
  ];

  return (
    <aside className="w-64 bg-[#0c101d] border-r border-slate-800/80 flex flex-col justify-between select-none h-screen sticky top-0">
      <div>
        {/* Brand Header */}
        <div className="p-4 flex items-center justify-between border-b border-slate-800/60">
          <div className="flex items-center gap-2.5">
            <div className="w-6 h-6 rounded-md bg-gradient-to-tr from-sky-500 to-indigo-500 flex items-center justify-center shadow-lg shadow-sky-500/20">
              <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
            </div>
            <div>
              <h1 className="font-semibold text-sm tracking-tight text-white flex items-center gap-1.5">
                RecallBox
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-sky-950/80 text-sky-400 border border-sky-800/50">Local</span>
              </h1>
            </div>
          </div>
        </div>

        {/* Quick Capture Button */}
        <div className="p-3">
          <button
            onClick={onOpenQuickCapture}
            className="w-full flex items-center justify-center gap-2 bg-sky-600 hover:bg-sky-500 text-white font-medium text-xs py-2 px-3 rounded-lg shadow-md shadow-sky-600/20 transition-all duration-150 active:scale-[0.98]"
          >
            <Plus className="w-4 h-4" />
            <span>Remember Something</span>
            <kbd className="ml-auto text-[10px] font-mono bg-sky-700/60 text-sky-200 px-1.5 py-0.5 rounded border border-sky-400/20">C</kbd>
          </button>
        </div>

        {/* Primary Views Navigation */}
        <div className="px-2 py-1.5 space-y-0.5">
          <div className="px-2.5 py-1 text-[11px] font-medium uppercase tracking-wider text-slate-400">Navigation</div>
          {mainNav.map(item => {
            const Icon = item.icon;
            const active = currentView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  onSelectView(item.id);
                  onSelectSourceType(undefined);
                }}
                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  active
                    ? 'bg-slate-800 text-sky-400 font-semibold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className={`w-4 h-4 ${active ? 'text-sky-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                {item.count !== undefined && item.count > 0 && (
                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded-full bg-sky-950 text-sky-400 border border-sky-800/40">
                    {item.count}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Sources Filters */}
        <div className="px-2 py-3 space-y-0.5 border-t border-slate-800/60 mt-2">
          <div className="px-2.5 py-1 text-[11px] font-medium uppercase tracking-wider text-slate-400">Sources</div>
          {sourceFilters.map(source => {
            const Icon = source.icon;
            const active = selectedSourceType === source.id;
            return (
              <button
                key={source.id}
                onClick={() => {
                  onSelectView('memories');
                  onSelectSourceType(active ? undefined : source.id);
                }}
                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs transition-colors ${
                  active
                    ? 'bg-slate-800 text-sky-400 font-semibold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className={`w-3.5 h-3.5 ${active ? 'text-sky-400' : 'text-slate-400'}`} />
                  <span>{source.label}</span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Footer Info */}
      <div className="p-3 border-t border-slate-800/60 bg-[#0a0e19]">
        <div className="flex items-center justify-between text-[11px] text-slate-400">
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            Offline & Local
          </span>
          <span className="font-mono text-[10px] text-slate-400">v0.1.0</span>
        </div>
      </div>
    </aside>
  );
};
