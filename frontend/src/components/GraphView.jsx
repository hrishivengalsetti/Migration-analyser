import React, { useMemo } from 'react';
import { ReactFlow, Controls, MiniMap, Background } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

export default function GraphView({ graphData, blastRadius }) {
  if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
    return (
      <div className="bg-white p-12 rounded-lg border border-gray-200 shadow-sm text-center">
        <h3 className="text-lg font-bold text-gray-700 mb-2">No Graph Data</h3>
        <p className="text-sm text-gray-500">No graph data available for this run.</p>
      </div>
    );
  }

  const { changed_symbols = [], directly_affected = [], transitively_affected = [] } = blastRadius || {};

  const changedSet = new Set(changed_symbols);
  const directSet = new Set(directly_affected);
  const transSet = new Set(transitively_affected);

  const { nodes, edges } = useMemo(() => {
    const rawNodes = graphData.nodes || [];
    const rawEdges = graphData.edges || [];

    // Group nodes into columns for deterministic layout
    const col0 = []; // changed
    const col1 = []; // directly affected
    const col2 = []; // transitively affected
    const col3 = []; // other

    rawNodes.forEach((node) => {
      if (changedSet.has(node.id)) {
        col0.push(node);
      } else if (directSet.has(node.id)) {
        col1.push(node);
      } else if (transSet.has(node.id)) {
        col2.push(node);
      } else {
        col3.push(node);
      }
    });

    const columns = [col0, col1, col2, col3];
    const columnX = [50, 320, 590, 860]; // x coordinates for columns

    const rfNodes = [];

    columns.forEach((colNodes, colIdx) => {
      const x = columnX[colIdx];
      colNodes.forEach((node, rowIdx) => {
        const y = 50 + rowIdx * 90; // vertical spacing

        let category = 'other';
        let style = {
          border: '2px solid #9ca3af',
          backgroundColor: '#f9fafb',
          color: '#374151',
          padding: '10px 14px',
          borderRadius: '8px',
          fontSize: '12px',
          fontWeight: '500',
          width: 220,
        };

        if (changedSet.has(node.id)) {
          category = 'changed';
          style = {
            ...style,
            border: '2px solid #ef4444',
            backgroundColor: '#fef2f2',
            color: '#991b1b',
            fontWeight: '700',
          };
        } else if (directSet.has(node.id)) {
          category = 'directly_affected';
          style = {
            ...style,
            border: '2px solid #f59e0b',
            backgroundColor: '#fffbeb',
            color: '#92400e',
            fontWeight: '600',
          };
        } else if (transSet.has(node.id)) {
          category = 'transitively_affected';
          style = {
            ...style,
            border: '2px solid #3b82f6',
            backgroundColor: '#eff6ff',
            color: '#1e40af',
            fontWeight: '600',
          };
        }

        const labelName = node.id.split('.').pop();

        rfNodes.push({
          id: node.id,
          position: { x, y },
          data: {
            label: (
              <div data-testid={`node-${node.id}`} data-category={category}>
                <div className="font-mono text-xs truncate" title={node.id}>
                  {labelName}
                </div>
                {node.kind && (
                  <div className="text-[10px] opacity-75 uppercase font-sans mt-0.5">
                    {node.kind}
                  </div>
                )}
              </div>
            ),
          },
          style,
        });
      });
    });

    // Map edges preserving caller -> callee direction
    const rfEdges = rawEdges.map((edge, idx) => ({
      id: `edge-${idx}`,
      source: edge.source,
      target: edge.target,
      label: edge.kind || '',
      animated: changedSet.has(edge.target),
      style: { stroke: changedSet.has(edge.target) ? '#ef4444' : '#6b7280', strokeWidth: 1.5 },
    }));

    return { nodes: rfNodes, edges: rfEdges };
  }, [graphData, blastRadius]);

  return (
    <div className="space-y-4" data-testid="graph-view">
      {/* Static AST Analysis Disclaimer */}
      <div
        className="p-3 bg-amber-50 border border-amber-200 rounded-md text-xs text-amber-800 flex items-center"
        data-testid="static-analysis-disclaimer"
      >
        <svg
          className="w-4 h-4 text-amber-600 mr-2 flex-shrink-0"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
        <span>
          <strong>⚠️ Static AST Analysis</strong> — dynamic calls, reflection, and runtime dispatch are not captured in this graph.
        </span>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-4 px-4 py-2 bg-white border border-gray-200 rounded-md text-xs">
        <span className="font-semibold text-gray-700">Legend:</span>
        <div className="flex items-center space-x-1.5">
          <span className="w-3 h-3 rounded-full bg-red-500 inline-block"></span>
          <span className="text-gray-600">Changed Symbol</span>
        </div>
        <div className="flex items-center space-x-1.5">
          <span className="w-3 h-3 rounded-full bg-amber-500 inline-block"></span>
          <span className="text-gray-600">Directly Affected</span>
        </div>
        <div className="flex items-center space-x-1.5">
          <span className="w-3 h-3 rounded-full bg-blue-500 inline-block"></span>
          <span className="text-gray-600">Transitively Affected</span>
        </div>
        <div className="flex items-center space-x-1.5">
          <span className="w-3 h-3 rounded-full bg-gray-400 inline-block"></span>
          <span className="text-gray-600">Unaffected</span>
        </div>
      </div>

      {/* Graph Container */}
      <div className="w-full h-[550px] bg-gray-50 border border-gray-200 rounded-lg overflow-hidden relative">
        <ReactFlow nodes={nodes} edges={edges} fitView>
          <Background color="#cbd5e1" gap={16} />
          <Controls />
          <MiniMap nodeStrokeWidth={3} zoomable pannable />
        </ReactFlow>
      </div>
    </div>
  );
}
