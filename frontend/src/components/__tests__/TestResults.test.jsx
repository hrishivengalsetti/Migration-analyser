import { describe, it, expect } from 'vitest';
import React from 'react';
import { render, screen } from '@testing-library/react';
import TestResults from '../TestResults';

const mockTestResults = [
  {
    test_id: 'tests/test_api.py::test_checkout',
    status_original: 'passed',
    status_migrated: 'passed',
    comparison: 'passed_both',
  },
  {
    test_id: 'tests/test_client.py::test_post_timeout',
    status_original: 'passed',
    status_migrated: 'failed',
    comparison: 'regression',
  },
];

describe('TestResults Component', () => {
  it('renders empty message when testResults is empty', () => {
    render(<TestResults testResults={[]} />);
    expect(screen.getByTestId('test-results-empty')).toBeInTheDocument();
    expect(screen.getByText('No tests were executed for this migration.')).toBeInTheDocument();
  });

  it('renders summary count header and table with comparison badges and regression highlighting', () => {
    render(<TestResults testResults={mockTestResults} />);

    expect(screen.getByTestId('test-results-component')).toBeInTheDocument();
    expect(screen.getByText('2 Total Tests')).toBeInTheDocument();
    expect(screen.getByText('1 Passed')).toBeInTheDocument();
    expect(screen.getByText('1 Regressions')).toBeInTheDocument();

    expect(screen.getByText('tests/test_api.py::test_checkout')).toBeInTheDocument();
    expect(screen.getByText('tests/test_client.py::test_post_timeout')).toBeInTheDocument();

    // Check regression row highlighting
    const regressionRow = screen.getByTestId('test-row-1');
    expect(regressionRow).toHaveClass('bg-red-50/70');
  });
});
