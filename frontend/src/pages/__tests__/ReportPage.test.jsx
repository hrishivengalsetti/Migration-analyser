import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import ReportPage from '../ReportPage';

const mockFullReport = {
  run_id: 'test-run-123',
  created_at: '2026-08-29T12:00:00Z',
  classification: 'regression_detected',
  summary: {
    total_files_changed: 3,
    total_symbols_changed: 5,
    total_affected_symbols: 12,
    total_tests_run: 8,
    regressions_count: 1,
  },
  ai_interpretation: {
    migration_intent: 'Migrated HTTP client implementation.',
    risk_summary: '1 regression detected in error handling.',
    key_concerns: ['Timeout behavior changed.'],
    confidence: 'high',
  },
  file_diffs: [
    {
      file: 'app/client.py',
      status: 'modified',
      original_content: 'def get(): pass',
      migrated_content: 'def get(): return True',
    },
  ],
  symbol_diffs: [
    {
      symbol_id: 'app.client.HttpClient.post',
      file: 'app/client.py',
      kind: 'method',
      change_kind: 'body_changed',
      original_source: 'def post(self): pass',
      migrated_source: 'def post(self): return 1',
      line_original: 42,
      line_migrated: 45,
    },
  ],
  blast_radius: {
    changed_symbols: ['app.client.HttpClient.post'],
    directly_affected: ['app.api.submit_order'],
    transitively_affected: ['app.views.checkout'],
    all_affected: ['app.client.HttpClient.post', 'app.api.submit_order', 'app.views.checkout'],
    cycles_detected: false,
    total_affected_count: 3,
  },
  graph_data: {
    nodes: [
      { id: 'app.client.HttpClient.post', kind: 'method', file: 'app/client.py' },
      { id: 'app.api.submit_order', kind: 'function', file: 'app/api.py' },
    ],
    edges: [
      { source: 'app.api.submit_order', target: 'app.client.HttpClient.post', kind: 'calls' },
    ],
  },
  test_results: [
    {
      test_id: 'tests/test_client.py::test_post_timeout',
      status_original: 'passed',
      status_migrated: 'failed',
      comparison: 'regression',
    },
  ],
  evidence: [
    {
      symbol_id: 'app.client.HttpClient.post',
      file: 'app/client.py',
      change_kind: 'body_changed',
      comparison: 'regression',
      failing_tests: ['tests/test_client.py::test_post_timeout'],
      passing_tests: ['tests/test_client.py::test_post_success'],
    },
  ],
};

describe('ReportPage Component All Tabs', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  const renderReportPage = (runId = 'test-run-123') => {
    return render(
      <MemoryRouter initialEntries={[`/report/${runId}`]}>
        <Routes>
          <Route path="/report/:runId" element={<ReportPage />} />
        </Routes>
      </MemoryRouter>
    );
  };

  it('renders Summary tab with metric cards and AI Narrative component', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockFullReport,
    });

    renderReportPage();

    await screen.findByText('Migration Analysis Report');

    expect(screen.getByTestId('files-changed')).toHaveTextContent('3');
    expect(screen.getByTestId('symbols-changed')).toHaveTextContent('5');
    expect(screen.getByTestId('blast-radius')).toHaveTextContent('12');
    expect(screen.getByTestId('regressions')).toHaveTextContent('1');
    expect(screen.getByTestId('tests-run')).toHaveTextContent('8');

    // AI Narrative in Summary tab
    expect(screen.getByText('AI-Generated Narrative')).toBeInTheDocument();
    expect(screen.getByText('Migrated HTTP client implementation.')).toBeInTheDocument();
  });

  it('navigates seamlessly across all 5 tabs: Summary, Changes, Impact, Tests, Evidence', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockFullReport,
    });

    renderReportPage();

    await screen.findByText('Migration Analysis Report');

    // 1. Changes tab
    fireEvent.click(screen.getByRole('button', { name: /Changes \(1\)/i }));
    expect(screen.getByText('File Diffs (1)')).toBeInTheDocument();

    // 2. Impact tab
    fireEvent.click(screen.getByRole('button', { name: /Impact Graph/i }));
    expect(screen.getByTestId('static-analysis-disclaimer')).toBeInTheDocument();

    // 3. Tests tab
    fireEvent.click(screen.getByRole('button', { name: /Test Results \(1\)/i }));
    expect(screen.getByTestId('test-results-component')).toBeInTheDocument();

    // 4. Evidence tab
    fireEvent.click(screen.getByRole('button', { name: /Evidence \(1\)/i }));
    expect(screen.getByTestId('evidence-panel-component')).toBeInTheDocument();
  });
});
