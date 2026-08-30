import { describe, it, expect } from 'vitest';
import React from 'react';
import { render, screen } from '@testing-library/react';
import AINarrative from '../AINarrative';

const mockInterpretation = {
  migration_intent: 'Migrated HTTP client implementation.',
  risk_summary: '1 regression detected in timeout handling.',
  key_concerns: ['Timeout behavior changed from 5s to 2s.'],
  confidence: 'high',
};

describe('AINarrative Component', () => {
  it('renders neutral empty message when interpretation is null/missing', () => {
    render(<AINarrative interpretation={null} />);
    expect(screen.getByTestId('ai-narrative-empty')).toBeInTheDocument();
    expect(screen.getByText('AI analysis is not available for this run.')).toBeInTheDocument();
  });

  it('renders migration intent, risk summary, key concerns, and confidence badge when interpretation is present', () => {
    render(<AINarrative interpretation={mockInterpretation} />);

    expect(screen.getByTestId('ai-narrative-component')).toBeInTheDocument();
    expect(screen.getByText('AI-Generated Narrative')).toBeInTheDocument();
    expect(screen.getByText('Confidence: high')).toBeInTheDocument();
    expect(screen.getByText('Migrated HTTP client implementation.')).toBeInTheDocument();
    expect(screen.getByText('1 regression detected in timeout handling.')).toBeInTheDocument();
    expect(screen.getByText('Timeout behavior changed from 5s to 2s.')).toBeInTheDocument();
  });
});
