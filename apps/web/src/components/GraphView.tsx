import React, { useEffect, useState, useRef } from 'react';
import { Share2, ZoomIn, ZoomOut, RotateCcw, Info, Sparkles, ArrowRight, ExternalLink } from 'lucide-react';
import { api } from '../lib/api';
import { GraphData, GraphNode, GraphEdge, Memory } from '../lib/types';

interface GraphViewProps {
  onSelectMemory: (id: string) => void;
}

export const GraphView: React.FC<GraphViewProps> = ({ onSelectMemory }) => {
  const [data, setData] = useState<GraphData>({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    async function load() {
      try {
        const res = await api.getGraphData();
        setData(res);
      } catch (e) {
        console.error('Failed to load graph data:', e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  // Compute 2D circular/force layout positions for nodes
  const nodePositions = React.useMemo(() => {
    const positions: Record<string, { x: number; y: number }> = {};
    const n = data.nodes.length;
    if (n === 0) return positions;

    const centerX = 400;
    const centerY = 300;
    const radius = Math.min(260, Math.max(120, n * 24));

    data.nodes.forEach((node, idx) => {
      const angle = (idx / n) * 2 * Math.PI;
      // Add slight jitter for natural look
      const jitter = (idx % 2 === 0 ? 1 : 0.85);
      positions[node.id] = {
        x: centerX + Math.cos(angle) * radius * jitter,
        y: centerY + Math.sin(angle) * radius * jitter
      };
    });

    return positions;
  }, [data.nodes]);

  const getNodeColor = (type: string) => {
    switch (type) {
      case 'repository': return '#c084fc'; // purple
      case 'video': return '#f87171'; // red
      case 'note': return '#fbbf24'; // amber
      case 'quote': return '#34d399'; // emerald
      default: return '#38bdf8'; // sky
    }
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.target === containerRef.current || (e.target as HTMLElement).tagName === 'svg') {
      setIsDragging(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
    }
  };

  const handleMouseUp = () => setIsDragging(false);

  return (
    <div className="flex-1 flex flex-col h-full bg-[#090d16] relative overflow-hidden select-none">
      {/* Top Controls Bar */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-[#0c101d] z-10">
        <div className="flex items-center gap-2">
          <Share2 className="w-4 h-4 text-sky-400" />
          <h2 className="font-semibold text-sm text-slate-100">Knowledge Graph</h2>
          <span className="text-xs text-slate-400 font-mono">
            ({data.nodes.length} memories, {data.edges.length} connections)
          </span>
        </div>

        <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 rounded-lg p-1">
          <button
            onClick={() => setZoom(z => Math.min(z + 0.2, 2.5))}
            className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setZoom(z => Math.max(z - 0.2, 0.4))}
            className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }); }}
            className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
            title="Reset View"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main Canvas Area */}
      <div
        ref={containerRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        className="flex-1 relative cursor-grab active:cursor-grabbing overflow-hidden flex items-center justify-center"
      >
        {loading ? (
          <div className="flex flex-col items-center justify-center text-slate-400 gap-2">
            <div className="w-6 h-6 border-2 border-sky-400/30 border-t-sky-400 rounded-full animate-spin" />
            <span className="text-xs">Mapping memory relationships...</span>
          </div>
        ) : data.nodes.length === 0 ? (
          <div className="text-center text-slate-400 text-xs">
            No memories saved yet. Save items to build your knowledge graph!
          </div>
        ) : (
          <svg
            className="w-full h-full"
            viewBox="0 0 800 600"
            style={{
              transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
              transformOrigin: 'center center',
              transition: isDragging ? 'none' : 'transform 0.1s ease-out'
            }}
          >
            {/* Draw Relationship Edges */}
            {data.edges.map((edge) => {
              const src = nodePositions[edge.source];
              const tgt = nodePositions[edge.target];
              if (!src || !tgt) return null;
              return (
                <g key={edge.id}>
                  <line
                    x1={src.x}
                    y1={src.y}
                    x2={tgt.x}
                    y2={tgt.y}
                    stroke="#334155"
                    strokeWidth={Math.max(1, edge.confidence * 2)}
                    strokeDasharray={edge.type === 'contradicts' ? '4 3' : undefined}
                    opacity={0.6}
                  />
                </g>
              );
            })}

            {/* Draw Memory Nodes */}
            {data.nodes.map((node) => {
              const pos = nodePositions[node.id];
              if (!pos) return null;
              const isSelected = selectedNode?.id === node.id;
              const nodeColor = getNodeColor(node.source_type);

              return (
                <g
                  key={node.id}
                  transform={`translate(${pos.x}, ${pos.y})`}
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedNode(node);
                  }}
                  className="cursor-pointer group"
                >
                  <circle
                    r={isSelected ? 16 : 10 + (node.importance || 0.5) * 6}
                    fill={nodeColor}
                    fillOpacity={isSelected ? 0.9 : 0.6}
                    stroke={isSelected ? '#ffffff' : nodeColor}
                    strokeWidth={isSelected ? 2.5 : 1}
                    className="transition-all duration-150 group-hover:scale-125"
                  />

                  <text
                    y={22}
                    textAnchor="middle"
                    fill="#94a3b8"
                    fontSize="10"
                    fontWeight="500"
                    className="group-hover:fill-sky-300 font-sans pointer-events-none select-none"
                  >
                    {node.label}
                  </text>
                </g>
              );
            })}
          </svg>
        )}

        {/* Selected Node Details Drawer */}
        {selectedNode && (
          <div className="absolute right-4 bottom-4 w-80 bg-[#0e1424]/95 border border-slate-700/80 rounded-xl p-4 shadow-2xl backdrop-blur-md animate-fade-in z-20">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-slate-800 text-sky-400 border border-slate-700">
                {selectedNode.source_type}
              </span>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-slate-400 hover:text-slate-200 text-xs"
              >
                ✕
              </button>
            </div>

            <h3 className="font-semibold text-sm text-slate-100 mb-2 leading-snug">
              {selectedNode.label}
            </h3>

            <div className="flex flex-wrap gap-1 mb-3">
              {selectedNode.tags.map(t => (
                <span key={t} className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                  #{t}
                </span>
              ))}
            </div>

            <button
              onClick={() => onSelectMemory(selectedNode.id)}
              className="w-full flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium transition-colors"
            >
              <span>Open Memory</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
