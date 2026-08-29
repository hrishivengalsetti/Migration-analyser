import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import ReportPage from '../ReportPage';

const mockReport = {
  run_id: 'test-run-123',
  created_at: '2026-08-29T12:00:00Z',
  classification: 'regression_detected',
  summary: {
    total_files_changed: 2,
    total_symbols_changed: 4,
    total_affected_symbols: 8,
    total_tests_run: 10,
    regressions_count: 1,
  },
  ai_interpretation: {
    migration_intent: 'Migrated HTTP client to httpx.',
    risk_summary: 'Found 1 regression in timeout handling.',
    key_concerns: ['Timeout behavior changed from 5s to 2s'],
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

describe('ReportPage Component', () => {
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
      json: async () => mockReport,
    });

    renderReportPage();

    expect(screen.getByText('Loading analysis report...')).toBeInTheDocument();

    expect(await screen.findByText('Migration Analysis Report')).toBeInTheDocument();
    expect(screen.getByText('REGRESSION DETECTED')).toBeInTheDocument();
    expect(screen.getByText('Migrated HTTP client to httpx.')).toBeInTheDocument();
  });

  it('renders error banner when report fetch fails with 404', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({ detail: 'Report not found' }),
    });

    renderReportPage('invalid-run-id');

    expect(await screen.findByText('Unable to Load Report')).toBeInTheDocument();
    expect(screen.getByText('Report not found')).toBeInTheDocument();
  });

  it('navigates between Summary and Changes tabs', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockReport,
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
  });
});
