import { describe, it, expect, vi } from 'vitest';
import React from 'react';
import { render, screen } from '@testing-library/react';
import GraphView from '../GraphView';

// Mock @xyflow/react components so JSDOM doesn't crash on canvas/webgl layout calls
vi.mock('@xyflow/react', () => {
  return {
    ReactFlow: ({ nodes, edges, children }) => (
      <div data-testid="react-flow-mock">
        <div data-testid="nodes-count">{nodes.length}</div>
        <div data-testid="edges-count">{edges.length}</div>
        {nodes.map((node) => (
          <div key={node.id} data-testid={`rf-node-${node.id}`}>
            {node.data.label}
          </div>
        ))}
        {edges.map((edge) => (
          <div key={edge.id} data-testid={`rf-edge-${edge.id}`} data-source={edge.source} data-target={edge.target}>
            {edge.label}
          </div>
        ))}
        {children}
      </div>
    ),
    Controls: () => <div data-testid="controls-mock" />,
    MiniMap: () => <div data-testid="minimap-mock" />,
    Background: () => <div data-testid="background-mock" />,
  };
});

const mockGraphData = {
  nodes: [
    { id: 'app.client.HttpClient.post', kind: 'method', file: 'app/client.py' },
    { id: 'app.api.submit_order', kind: 'function', file: 'app/api.py' },
    { id: 'app.views.checkout', kind: 'function', file: 'app/views.py' },
    { id: 'app.utils.helpers', kind: 'module', file: 'app/utils.py' },
  ],
  edges: [
    { source: 'app.api.submit_order', target: 'app.client.HttpClient.post', kind: 'calls' },
    { source: 'app.views.checkout', target: 'app.api.submit_order', kind: 'calls' },
  ],
};

const mockBlastRadius = {
  changed_symbols: ['app.client.HttpClient.post'],
  directly_affected: ['app.api.submit_order'],
  transitively_affected: ['app.views.checkout'],
  all_affected: ['app.client.HttpClient.post', 'app.api.submit_order', 'app.views.checkout'],
  cycles_detected: false,
  total_affected_count: 3,
};

describe('GraphView Component', () => {
  it('renders empty message when graphData is missing or empty', () => {
    render(<GraphView graphData={null} blastRadius={null} />);
    expect(screen.getByText('No Graph Data')).toBeInTheDocument();
    expect(screen.getByText('No graph data available for this run.')).toBeInTheDocument();
  });

  it('renders static AST analysis disclaimer banner', () => {
    render(<GraphView graphData={mockGraphData} blastRadius={mockBlastRadius} />);
    const disclaimer = screen.getByTestId('static-analysis-disclaimer');
    expect(disclaimer).toBeInTheDocument();
    expect(disclaimer).toHaveTextContent('Static AST Analysis');
    expect(disclaimer).toHaveTextContent('dynamic calls, reflection, and runtime dispatch are not captured in this graph.');
  });

  it('categorizes nodes correctly into changed, directly_affected, transitively_affected, and other', () => {
    render(<GraphView graphData={mockGraphData} blastRadius={mockBlastRadius} />);

    expect(screen.getByTestId('node-app.client.HttpClient.post')).toHaveAttribute('data-category', 'changed');
    expect(screen.getByTestId('node-app.api.submit_order')).toHaveAttribute('data-category', 'directly_affected');
    expect(screen.getByTestId('node-app.views.checkout')).toHaveAttribute('data-category', 'transitively_affected');
    expect(screen.getByTestId('node-app.utils.helpers')).toHaveAttribute('data-category', 'other');
  });

  it('preserves caller -> callee edge direction exactly', () => {
    render(<GraphView graphData={mockGraphData} blastRadius={mockBlastRadius} />);

    const edge0 = screen.getByTestId('rf-edge-edge-0');
    expect(edge0).toHaveAttribute('data-source', 'app.api.submit_order');
    expect(edge0).toHaveAttribute('data-target', 'app.client.HttpClient.post');

    const edge1 = screen.getByTestId('rf-edge-edge-1');
    expect(edge1).toHaveAttribute('data-source', 'app.views.checkout');
    expect(edge1).toHaveAttribute('data-target', 'app.api.submit_order');
  });
});
