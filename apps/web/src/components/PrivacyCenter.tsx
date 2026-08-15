import React, { useEffect, useState } from 'react';
import { Shield, Download, Upload, Trash2, HardDrive, Cpu, Lock, FileCode, AlertTriangle, X } from 'lucide-react';
import { api } from '../lib/api';
import { PrivacyStats } from '../lib/types';

export const PrivacyCenter: React.FC = () => {
  const [stats, setStats] = useState<PrivacyStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [importStatus, setImportStatus] = useState<string | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [showPurgeModal, setShowPurgeModal] = useState(false);
  const [confirmPhraseInput, setConfirmPhraseInput] = useState('');
  const [isPurging, setIsPurging] = useState(false);

  const loadStats = async () => {
    try {
      const res = await api.getPrivacyStats();
      setStats(res);
    } catch (e) {
      console.error('Failed to load privacy stats:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>, type: 'bookmarks' | 'json') => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsImporting(true);
    setImportStatus('Importing file into local RecallBox database...');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const endpoint = type === 'bookmarks' ? '/api/v1/import/bookmarks' : '/api/v1/import/json';
      const token = await api.getPrivacyStats().catch(() => null); // ensure session
      const headers: Record<string, string> = {};
      const localToken = localStorage.getItem('recallbox_token');
      if (localToken) headers['X-RecallBox-Key'] = localToken;

      const res = await fetch(endpoint, {
        method: 'POST',
        headers,
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        setImportStatus(`✓ Successfully imported ${data.imported_count} memories!`);
        loadStats();
      } else {
        setImportStatus(`Import failed: ${data.detail || 'Unknown error'}`);
      }
    } catch (err: any) {
      setImportStatus(`Import error: ${err.message}`);
    } finally {
      setIsImporting(false);
    }
  };

  const executePurge = async () => {
    if (confirmPhraseInput.trim() !== 'PERMANENTLY PURGE ALL DATA') {
      alert('Confirmation phrase does not match "PERMANENTLY PURGE ALL DATA".');
      return;
    }

    setIsPurging(true);
    try {
      await api.purgeAllData('PERMANENTLY PURGE ALL DATA');
      setShowPurgeModal(false);
      setConfirmPhraseInput('');
      loadStats();
      alert('All local database records have been permanently purged.');
    } catch (err: any) {
      alert(`Purge failed: ${err.message}`);
    } finally {
      setIsPurging(false);
    }
  };

  return (
    <div className="flex-1 p-6 space-y-6 overflow-y-auto max-w-4xl mx-auto w-full">
      {/* Header */}
      <div className="border-b border-slate-800 pb-5">
        <div className="flex items-center gap-2 text-emerald-400 mb-1">
          <Shield className="w-5 h-5" />
          <span className="text-xs font-mono uppercase tracking-widest font-semibold">Local-First Assurance</span>
        </div>
        <h2 className="text-2xl font-bold text-slate-100 tracking-tight">Privacy & Data Ownership Center</h2>
        <p className="text-xs text-slate-400 mt-1">
          Your personal memories belong exclusively to you. No mandatory accounts, no cloud lock-in, and zero unsolicited telemetry.
        </p>
      </div>

      {loading ? (
        <div className="py-16 text-center text-slate-400 text-xs">
          Loading privacy audit statistics...
        </div>
      ) : stats ? (
        <div className="space-y-6">
          {/* Storage & Privacy Stat Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-[#0e1424] border border-slate-800">
              <span className="text-xs text-slate-400 flex items-center gap-1.5">
                <HardDrive className="w-3.5 h-3.5 text-sky-400" />
                Local Memories
              </span>
              <div className="text-xl font-bold text-slate-100 mt-1 font-mono">{stats.stored_memories_count}</div>
              <span className="text-[10px] text-slate-400 font-mono">SQLite (FTS5 indexed)</span>
            </div>

            <div className="p-4 rounded-xl bg-[#0e1424] border border-slate-800">
              <span className="text-xs text-slate-400 flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-purple-400" />
                AI Provider
              </span>
              <div className="text-xl font-bold text-purple-300 mt-1 uppercase font-mono">{stats.active_ai_provider}</div>
              <span className="text-[10px] text-emerald-400 font-mono">Offline-ready</span>
            </div>

            <div className="p-4 rounded-xl bg-[#0e1424] border border-slate-800">
              <span className="text-xs text-slate-400 flex items-center gap-1.5">
                <Lock className="w-3.5 h-3.5 text-emerald-400" />
                Telemetry
              </span>
              <div className="text-xl font-bold text-emerald-400 mt-1 font-mono">OFF</div>
              <span className="text-[10px] text-slate-400 font-mono">0 bytes sent</span>
            </div>

            <div className="p-4 rounded-xl bg-[#0e1424] border border-slate-800">
              <span className="text-xs text-slate-400 flex items-center gap-1.5">
                <HardDrive className="w-3.5 h-3.5 text-amber-400" />
                DB File Size
              </span>
              <div className="text-xl font-bold text-amber-300 mt-1 font-mono">
                {Math.round(stats.db_size_bytes / 1024)} KB
              </div>
              <span className="text-[10px] text-slate-400 font-mono">recallbox.db</span>
            </div>
          </div>

          {/* Export Section */}
          <div className="p-5 rounded-xl bg-[#0e1424] border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                  <Download className="w-4 h-4 text-sky-400" />
                  Full Export (Never Trapped)
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Export your entire database to a standalone ZIP archive containing individual Markdown files with YAML frontmatter, JSON data, and knowledge graph.
                </p>
              </div>

              <a
                href={api.getExportZipUrl()}
                download="recallbox-export.zip"
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold shadow-md shadow-sky-600/20 transition-colors"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Export ZIP</span>
              </a>
            </div>
          </div>

          {/* Import Section */}
          <div className="p-5 rounded-xl bg-[#0e1424] border border-slate-800 space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                <Upload className="w-4 h-4 text-purple-400" />
                Import Existing Data
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Seamlessly import bookmarks from Chrome, Brave, Firefox, Edge, Safari, Pocket, or RecallBox JSON backups.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <label className="p-4 rounded-lg bg-slate-900/80 border border-slate-800 hover:border-slate-700 cursor-pointer flex items-center justify-between transition-colors">
                <div>
                  <div className="text-xs font-medium text-slate-200">Import HTML Bookmarks</div>
                  <div className="text-[11px] text-slate-400">Chrome, Firefox, Safari exports</div>
                </div>
                <input
                  type="file"
                  accept=".html,.htm"
                  onChange={(e) => handleFileUpload(e, 'bookmarks')}
                  className="hidden"
                  disabled={isImporting}
                />
                <Upload className="w-4 h-4 text-slate-400" />
              </label>

              <label className="p-4 rounded-lg bg-slate-900/80 border border-slate-800 hover:border-slate-700 cursor-pointer flex items-center justify-between transition-colors">
                <div>
                  <div className="text-xs font-medium text-slate-200">Import RecallBox JSON</div>
                  <div className="text-[11px] text-slate-400">JSON array backup dump</div>
                </div>
                <input
                  type="file"
                  accept=".json"
                  onChange={(e) => handleFileUpload(e, 'json')}
                  className="hidden"
                  disabled={isImporting}
                />
                <FileCode className="w-4 h-4 text-slate-400" />
              </label>
            </div>

            {importStatus && (
              <div className="p-3 rounded-lg bg-slate-900 text-xs font-mono text-sky-300 border border-slate-800">
                {importStatus}
              </div>
            )}
          </div>

          {/* Danger Zone */}
          <div className="p-5 rounded-xl bg-red-950/20 border border-red-900/40 space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-red-300 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-red-400" />
                  Danger Zone
                </h3>
                <p className="text-xs text-red-200/70 mt-0.5">
                  Permanently erase all memories, embeddings, and indices from your local database. Requires explicit confirmation phrase.
                </p>
              </div>

              <button
                onClick={() => setShowPurgeModal(true)}
                className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-red-900/60 hover:bg-red-800 text-red-200 text-xs font-semibold border border-red-700/60 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Purge All Data...</span>
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {/* Confirmation Modal */}
      {showPurgeModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0e1424] border border-red-500/50 w-full max-w-md rounded-xl p-5 shadow-2xl space-y-4 animate-fade-in">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-red-400 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" />
                Confirm Permanent Purge
              </h3>
              <button onClick={() => setShowPurgeModal(false)} className="text-slate-400 hover:text-slate-200">
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              This action is <strong className="text-red-300">irreversible</strong>. All memories, embeddings, tags, and SQLite search indices will be permanently destroyed.
            </p>

            <div className="space-y-1.5">
              <label className="block text-[11px] font-mono text-slate-400">
                Type <strong className="text-slate-200">PERMANENTLY PURGE ALL DATA</strong> to confirm:
              </label>
              <input
                type="text"
                autoFocus
                value={confirmPhraseInput}
                onChange={(e) => setConfirmPhraseInput(e.target.value)}
                placeholder="PERMANENTLY PURGE ALL DATA"
                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-xs font-mono text-white focus:outline-none focus:border-red-500"
              />
            </div>

            <div className="pt-2 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowPurgeModal(false)}
                className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 text-xs font-medium hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={confirmPhraseInput !== 'PERMANENTLY PURGE ALL DATA' || isPurging}
                onClick={executePurge}
                className="px-4 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-xs font-bold transition-colors"
              >
                {isPurging ? 'Purging...' : 'Permanently Delete Everything'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
