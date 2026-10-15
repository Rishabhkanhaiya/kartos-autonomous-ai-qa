import React, { useState, useMemo, useEffect, useRef } from 'react';
import { 
  Network, 
  ZoomIn, 
  ZoomOut, 
  Maximize2, 
  Bug, 
  Layers, 
  ArrowRight,
  CheckCircle,
  AlertTriangle,
  X
} from 'lucide-react';

export default function StateGraphView({
  graph = { nodes: [], edges: [], current_node_id: null },
  onSelectNode
}) {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 20, y: 20 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [selectedNode, setSelectedNode] = useState(null);
  const canvasRef = useRef(null);

  // Card dimensions
  const CARD_WIDTH = 185;
  const CARD_HEIGHT = 105;

  // Position nodes dynamically in an organized grid/flow layout
  const nodePositions = useMemo(() => {
    const positions = {};
    const nodes = graph.nodes || [];
    const count = nodes.length;

    if (count === 0) return positions;

    // Arrange in an aesthetically balanced horizontal flow with branching
    nodes.forEach((node, index) => {
      // 2 columns per row for compact viewports, or flow horizontally
      const col = index % 3;
      const row = Math.floor(index / 3);
      const x = 40 + col * 230 + (row % 2 === 1 ? 30 : 0);
      const y = 80 + row * 180;
      positions[node.id] = { x, y };
    });

    return positions;
  }, [graph.nodes]);

  // Auto-fit to screen whenever new nodes are added
  const autoFitView = () => {
    if (!canvasRef.current || !graph.nodes || graph.nodes.length === 0) return;
    
    const containerWidth = canvasRef.current.clientWidth || 600;
    const containerHeight = canvasRef.current.clientHeight || 450;

    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;

    Object.values(nodePositions).forEach(pos => {
      minX = Math.min(minX, pos.x);
      minY = Math.min(minY, pos.y);
      maxX = Math.max(maxX, pos.x + CARD_WIDTH);
      maxY = Math.max(maxY, pos.y + CARD_HEIGHT);
    });

    if (minX === Infinity) return;

    const contentWidth = maxX - minX + 60;
    const contentHeight = maxY - minY + 60;

    const scaleX = (containerWidth - 60) / contentWidth;
    const scaleY = (containerHeight - 60) / contentHeight;
    const newZoom = Math.min(Math.max(Math.min(scaleX, scaleY), 0.65), 1.05);

    const centerX = (containerWidth - contentWidth * newZoom) / 2;
    const centerY = (containerHeight - contentHeight * newZoom) / 2;

    setZoom(newZoom);
    setPan({
      x: Math.round(centerX - minX * newZoom + 20),
      y: Math.round(centerY - minY * newZoom + 20)
    });
  };

  useEffect(() => {
    if (graph.nodes && graph.nodes.length > 0) {
      autoFitView();
    }
  }, [graph.nodes?.length]);

  const handleMouseDown = (e) => {
    if (e.target.tagName === 'svg' || e.target.id === 'graph-canvas') {
      setIsDragging(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e) => {
    if (isDragging) {
      setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
    }
  };

  const handleMouseUp = () => setIsDragging(false);

  return (
    <div 
      className="flex-1 h-full flex flex-col bg-[#080C15] relative overflow-hidden select-none min-w-0"
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
    >
      {/* Top Header */}
      <div className="h-10 px-4 bg-[#0E1322] border-b border-[#1E293B] flex items-center justify-between z-10 shrink-0">
        <div className="flex items-center gap-2">
          <Network className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-bold uppercase tracking-wider text-slate-200">
            Directed State-Graph
          </span>
          <span className="text-[10px] font-mono text-slate-400 bg-slate-900 border border-slate-800 px-2 py-0.5 rounded ml-1">
            {graph.nodes?.length || 0} States &bull; {graph.edges?.length || 0} Edges
          </span>
        </div>

        {/* Zoom & Canvas Controls */}
        <div className="flex items-center gap-1.5 bg-[#090D16] border border-[#1E293B] p-1 rounded-lg">
          <button
            onClick={() => setZoom((z) => Math.min(z + 0.15, 2.0))}
            className="p-1 text-slate-400 hover:text-cyan-300 rounded transition"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <span className="text-[10px] font-mono text-slate-400 px-1">
            {Math.round(zoom * 100)}%
          </span>
          <button
            onClick={() => setZoom((z) => Math.max(z - 0.15, 0.4))}
            className="p-1 text-slate-400 hover:text-cyan-300 rounded transition"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={autoFitView}
            className="p-1 text-slate-400 hover:text-cyan-300 rounded transition border-l border-slate-800 pl-1.5"
            title="Auto-Fit to Screen"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* SVG Canvas Area */}
      <div 
        ref={canvasRef}
        id="graph-canvas" 
        className="flex-1 w-full h-full relative cursor-grab active:cursor-grabbing overflow-hidden"
      >
        {graph.nodes?.length === 0 ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none text-slate-600 space-y-2">
            <Layers className="w-10 h-10 stroke-[1.5] text-slate-700 animate-pulse" />
            <p className="text-xs font-medium text-slate-500">State Graph Empty</p>
            <p className="text-[11px] text-slate-600">Discovered UI mutations will populate this directed graph in real time.</p>
          </div>
        ) : (
          <svg
            className="w-full h-full"
            style={{
              transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
              transformOrigin: '0 0',
              transition: isDragging ? 'none' : 'transform 0.15s ease-out'
            }}
          >
            <defs>
              <marker
                id="arrowhead"
                markerWidth="8"
                markerHeight="6"
                refX="7"
                refY="3"
                orient="auto"
              >
                <polygon points="0 0, 8 3, 0 6" fill="#00F2FE" />
              </marker>
            </defs>

            {/* Render Directed Edges */}
            {graph.edges?.map((edge, index) => {
              const fromPos = nodePositions[edge.from];
              const toPos = nodePositions[edge.to];
              if (!fromPos || !toPos) return null;

              const isSelfLoop = edge.from === edge.to;
              if (isSelfLoop) {
                // Loop neatly above the card center
                const cx = fromPos.x + CARD_WIDTH / 2;
                const cy = fromPos.y;
                return (
                  <path
                    key={edge.id || index}
                    d={`M ${cx - 25} ${cy} C ${cx - 25} ${cy - 35}, ${cx + 25} ${cy - 35}, ${cx + 25} ${cy - 2}`}
                    fill="none"
                    stroke="#00F2FE"
                    strokeWidth="1.5"
                    strokeDasharray="4 2"
                    markerEnd="url(#arrowhead)"
                  />
                );
              }

              // Connecting transition arrow between distinct states
              const startX = fromPos.x + CARD_WIDTH;
              const startY = fromPos.y + 45;
              const endX = toPos.x - 2;
              const endY = toPos.y + 45;

              const dx = endX - startX;
              const cx1 = startX + dx * 0.4;
              const cy1 = startY;
              const cx2 = startX + dx * 0.6;
              const cy2 = endY;

              return (
                <g key={edge.id || index}>
                  <path
                    d={`M ${startX} ${startY} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${endX} ${endY}`}
                    fill="none"
                    stroke="#38BDF8"
                    strokeWidth="2"
                    opacity="0.8"
                    markerEnd="url(#arrowhead)"
                  />
                  {edge.target_description && (
                    <text
                      x={(startX + endX) / 2}
                      y={(startY + endY) / 2 - 8}
                      fill="#94A3B8"
                      fontSize="9"
                      fontFamily="monospace"
                      textAnchor="middle"
                    >
                      {edge.target_description.slice(0, 18)}
                    </text>
                  )}
                </g>
              );
            })}

            {/* Render State Nodes */}
            {graph.nodes?.map((node) => {
              const pos = nodePositions[node.id];
              if (!pos) return null;

              const isCurrent = graph.current_node_id === node.id;
              const hasBugs = node.is_buggy;

              return (
                <foreignObject
                  key={node.id}
                  x={pos.x}
                  y={pos.y}
                  width={CARD_WIDTH}
                  height={CARD_HEIGHT}
                  className="overflow-visible"
                >
                  <div
                    onClick={() => setSelectedNode(node)}
                    style={{ width: `${CARD_WIDTH}px` }}
                    className={`p-2.5 rounded-xl border transition-all cursor-pointer relative shadow-xl backdrop-blur-md select-none ${
                      hasBugs
                        ? 'bg-[#1a0c14]/90 border-rose-500 shadow-rose-950/60 ring-1 ring-rose-500/50'
                        : isCurrent
                        ? 'bg-[#0E1729]/95 border-cyan-400 shadow-cyan-950/60 ring-2 ring-cyan-400/50'
                        : 'bg-[#0E1322]/90 border-[#1E293B] hover:border-slate-600'
                    }`}
                  >
                    {/* Header */}
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="font-mono text-[10px] font-bold text-slate-300 uppercase tracking-wide">
                        {node.id}
                      </span>
                      {hasBugs ? (
                        <span className="flex items-center gap-1 text-[9px] font-mono text-rose-300 bg-rose-950/80 border border-rose-800/80 px-1.5 py-0.5 rounded font-bold">
                          <Bug className="w-2.5 h-2.5 text-rose-400 shrink-0" />
                          <span>{node.bug_count} Bug{node.bug_count > 1 ? 's' : ''}</span>
                        </span>
                      ) : isCurrent ? (
                        <span className="text-[9px] font-mono text-cyan-400 bg-cyan-950/70 border border-cyan-800 px-1.5 py-0.5 rounded font-bold">
                          ACTIVE
                        </span>
                      ) : (
                        <span className="text-[9px] font-mono text-slate-500">
                          v:{node.visits}
                        </span>
                      )}
                    </div>

                    {/* Title / URL */}
                    <h4 className="text-[11px] font-semibold text-slate-200 truncate" title={node.title}>
                      {node.title || 'Application State'}
                    </h4>

                    {/* Hash & Count */}
                    <div className="mt-2 pt-1.5 border-t border-slate-800/80 flex items-center justify-between text-[9px] font-mono text-slate-400">
                      <span className="truncate max-w-[70px]" title={node.state_hash}>
                        #{node.state_hash?.slice(0, 6)}
                      </span>
                      <span className="text-cyan-400 font-semibold">
                        {node.element_count} marks
                      </span>
                    </div>
                  </div>
                </foreignObject>
              );
            })}
          </svg>
        )}
      </div>

      {/* Selected Node Details Drawer */}
      {selectedNode && (
        <div className="absolute top-12 right-4 w-72 bg-[#0E1322]/95 backdrop-blur-md border border-[#1E293B] rounded-xl p-4 shadow-2xl z-30 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-cyan-400 font-mono">
                {selectedNode.id}
              </span>
              <span className="text-[10px] font-mono text-slate-400">
                #{selectedNode.state_hash?.slice(0, 8)}
              </span>
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-slate-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div>
            <label className="text-[10px] uppercase font-mono text-slate-500 font-semibold block">URL Path</label>
            <p className="text-xs font-mono text-slate-300 truncate">{selectedNode.url}</p>
          </div>

          {selectedNode.screenshot_b64 && (
            <div>
              <label className="text-[10px] uppercase font-mono text-slate-500 font-semibold block mb-1">State Snapshot</label>
              <img
                src={`data:image/png;base64,${selectedNode.screenshot_b64}`}
                alt="State Snapshot"
                className="w-full h-28 object-cover rounded-lg border border-slate-800"
              />
            </div>
          )}

          <div className="grid grid-cols-2 gap-2 text-center">
            <div className="bg-[#090D16] p-2 rounded-lg border border-slate-800">
              <div className="text-[10px] text-slate-500 font-mono">Interactive Marks</div>
              <div className="text-sm font-bold text-cyan-400 font-mono">{selectedNode.element_count}</div>
            </div>
            <div className="bg-[#090D16] p-2 rounded-lg border border-slate-800">
              <div className="text-[10px] text-slate-500 font-mono">Bugs Discovered</div>
              <div className={`text-sm font-bold font-mono ${selectedNode.bug_count > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                {selectedNode.bug_count}
              </div>
            </div>
          </div>

          {selectedNode.bugs?.length > 0 && (
            <div>
              <label className="text-[10px] uppercase font-mono text-rose-400 font-semibold block mb-1">Verified Anomalies</label>
              <ul className="space-y-1 text-xs text-rose-300">
                {selectedNode.bugs.map((b, i) => (
                  <li key={i} className="flex items-start gap-1 bg-rose-950/40 p-1.5 rounded border border-rose-900/60 font-mono text-[11px]">
                    <Bug className="w-3.5 h-3.5 shrink-0 mt-0.5 text-rose-400" />
                    <span>{b}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
