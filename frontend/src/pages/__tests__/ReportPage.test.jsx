import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import ReportPage from '../ReportPage';

const mockReportWithRegressions = {
  run_id: 'test-run-123',
  created_at: '2026-08-29T12:00:00Z',
  classification: 'regression_detected',
  summary: {
    total_files_changed: 3,
    total_symbols_changed: 5,
    total_affected_symbols: 12,
    total_tests_run: 8,
    regressions_count: 2,
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
      symbol_id: 'app.client.get',
      file: 'app/client.py',
      kind: 'function',
      change_kind: 'body_changed',
      original_source: 'def get(): pass',
      migrated_source: 'def get(): return True',
      line_original: 10,
      line_migrated: 10,
    },
  ],
};

const mockReportVerified = {
  run_id: 'verified-run-999',
  created_at: '2026-08-29T12:00:00Z',
  classification: 'verified',
  summary: {
    total_files_changed: 1,
    total_symbols_changed: 2,
    total_affected_symbols: 2,
    total_tests_run: 5,
    regressions_count: 0,
  },
  file_diffs: [],
  symbol_diffs: [],
};

describe('ReportPage & Summary/Changes Tabs', () => {
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

  it('renders loading state initially and then displays report data', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockReportWithRegressions,
    });

    renderReportPage();

    expect(screen.getByText('Loading analysis report...')).toBeInTheDocument();

    expect(await screen.findByText('Migration Analysis Report')).toBeInTheDocument();
    expect(screen.getByText('REGRESSION DETECTED')).toBeInTheDocument();
  });

  it('correctly displays deterministic backend summary metrics without fallback expressions', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockReportWithRegressions,
    });

    renderReportPage();

    await screen.findByText('Migration Analysis Report');

    expect(screen.getByTestId('files-changed')).toHaveTextContent('3');
    expect(screen.getByTestId('symbols-changed')).toHaveTextContent('5');
    expect(screen.getByTestId('blast-radius')).toHaveTextContent('12');
    expect(screen.getByTestId('regressions')).toHaveTextContent('2');
    expect(screen.getByTestId('tests-run')).toHaveTextContent('8');

    // Verify red visual emphasis when regressions_count > 0
    expect(screen.getByTestId('regressions')).toHaveClass('text-red-600');
  });

  it('displays regressions_count = 0 without red text highlight', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockReportVerified,
    });

    renderReportPage('verified-run-999');

    await screen.findByText('Migration Analysis Report');

    expect(screen.getByTestId('regressions')).toHaveTextContent('0');
    expect(screen.getByTestId('regressions')).toHaveClass('text-gray-900');
  });

  it('renders error state when report fetch fails with 404', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({ detail: 'Report not found' }),
    });

    renderReportPage('invalid-run-id');

    expect(await screen.findByText('Unable to Load Report')).toBeInTheDocument();
    expect(screen.getByText('Report not found')).toBeInTheDocument();
  });

  it('navigates to Changes tab and expands file & symbol diffs', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockReportWithRegressions,
    });

    renderReportPage();

    await screen.findByText('Migration Analysis Report');

    // Click Changes tab
    const changesTabBtn = screen.getByRole('button', { name: /Changes \(1\)/i });
    fireEvent.click(changesTabBtn);

    expect(screen.getByText('File Diffs (1)')).toBeInTheDocument();
    expect(screen.getByText('app/client.py')).toBeInTheDocument();

    // Toggle File Diff
    const showDiffBtn = screen.getByText('Show Diff ▼');
    fireEvent.click(showDiffBtn);

    expect(screen.getByText('def get(): return True')).toBeInTheDocument();

    // Toggle Symbol Diff
    const showSourceBtn = screen.getByText('Show Source ▼');
    fireEvent.click(showSourceBtn);

    expect(screen.getByText('app.client.get')).toBeInTheDocument();
  });
});
