import { describe, it, expect } from 'vitest';
import React from 'react';
import { render, screen } from '@testing-library/react';
import EvidencePanel from '../EvidencePanel';

const mockEvidence = [
  {
    symbol_id: 'app.client.HttpClient.post',
    file: 'app/client.py',
    change_kind: 'body_changed',
    comparison: 'regression',
    failing_tests: ['tests/test_client.py::test_post_timeout'],
    passing_tests: ['tests/test_client.py::test_post_success'],
  },
  {
    symbol_id: 'app.api.get_user',
    file: 'app/api.py',
    change_kind: 'added',
    comparison: 'verified',
    failing_tests: [],
    passing_tests: ['tests/test_api.py::test_get_user'],
  },
];

describe('EvidencePanel Component', () => {
  it('renders empty message when evidence is empty', () => {
    render(<EvidencePanel evidence={[]} />);
    expect(screen.getByTestId('evidence-empty')).toBeInTheDocument();
    expect(screen.getByText('No symbol changes detected in this migration.')).toBeInTheDocument();
  });

  it('renders evidence cards with change_kind and comparison badges, passing/failing tests, and regression highlighting', () => {
    render(<EvidencePanel evidence={mockEvidence} />);

    expect(screen.getByTestId('evidence-panel-component')).toBeInTheDocument();
    expect(screen.getByText('app.client.HttpClient.post')).toBeInTheDocument();
    expect(screen.getByText('app.api.get_user')).toBeInTheDocument();

    expect(screen.getByTestId('evidence-badge-0')).toHaveTextContent('✗ Regression');
    expect(screen.getByTestId('evidence-badge-1')).toHaveTextContent('✓ Verified');

    expect(screen.getByText('tests/test_client.py::test_post_timeout')).toBeInTheDocument();
    expect(screen.getByText('tests/test_client.py::test_post_success')).toBeInTheDocument();

    // Verify regression card border
    expect(screen.getByTestId('evidence-card-0')).toHaveClass('border-red-400');
  });
});
