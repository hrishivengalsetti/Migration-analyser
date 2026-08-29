import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import UploadPage from '../UploadPage';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('UploadPage & Upload Workflow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers({ shouldAdvanceTime: true });
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  const renderUploadPage = () => {
    return render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="/report/:runId" element={<div>Report View</div>} />
        </Routes>
      </MemoryRouter>
    );
  };

  it('renders upload inputs and submit button disabled by default (both files required)', () => {
    renderUploadPage();

    expect(screen.getByText('Original Codebase (.zip)')).toBeInTheDocument();
    expect(screen.getByText('Migrated Codebase (.zip)')).toBeInTheDocument();

    const submitBtn = screen.getByRole('button', { name: /Analyze Migration/i });
    expect(submitBtn).toBeDisabled();
  });

  it('validates non-ZIP files and prevents submit button activation', async () => {
    renderUploadPage();

    const originalInput = screen.getByTestId('original-file-input');
    const txtFile = new File(['hello'], 'original.txt', { type: 'text/plain' });

    fireEvent.change(originalInput, { target: { files: [txtFile] } });

    expect(await screen.findByText('Please select a valid .zip file')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Analyze Migration/i })).toBeDisabled();
  });

  it('enables submit button when valid ZIP files are selected for both original and migrated', () => {
    renderUploadPage();

    const originalInput = screen.getByTestId('original-file-input');
    const migratedInput = screen.getByTestId('migrated-file-input');

    const origZip = new File(['dummy'], 'original.zip', { type: 'application/zip' });
    const migZip = new File(['dummy'], 'migrated.zip', { type: 'application/zip' });

    fireEvent.change(originalInput, { target: { files: [origZip] } });
    fireEvent.change(migratedInput, { target: { files: [migZip] } });

    const submitBtn = screen.getByRole('button', { name: /Analyze Migration/i });
    expect(submitBtn).not.toBeDisabled();
  });

  it('handles successful POST /api/runs, receives run_id, polls status every 1000ms, and navigates on complete', async () => {
    // 1. Mock upload response
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ run_id: 'test-run-123', status: 'pending' }),
    });

    // 2. Mock polling responses
    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'analyzing' }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'executing' }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'complete' }),
      });

    renderUploadPage();

    const originalInput = screen.getByTestId('original-file-input');
    const migratedInput = screen.getByTestId('migrated-file-input');

    const origZip = new File(['dummy'], 'original.zip', { type: 'application/zip' });
    const migZip = new File(['dummy'], 'migrated.zip', { type: 'application/zip' });

    fireEvent.change(originalInput, { target: { files: [origZip] } });
    fireEvent.change(migratedInput, { target: { files: [migZip] } });

    const submitBtn = screen.getByRole('button', { name: /Analyze Migration/i });

    await act(async () => {
      fireEvent.click(submitBtn);
    });

    expect(global.fetch).toHaveBeenLastCalledWith('/api/runs', expect.objectContaining({
      method: 'POST',
    }));

    // Check status progress initialized
    expect(await screen.findByText('Initializing run...')).toBeInTheDocument();

    // Advance 1000ms -> analyzing
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
    });
    expect(await screen.findByText('Analyzing AST diffs & call graph...')).toBeInTheDocument();

    // Advance 1000ms -> executing
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
    });
    expect(await screen.findByText('Executing sandboxed tests in Docker...')).toBeInTheDocument();

    // Advance 1000ms -> complete
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
    });
    expect(await screen.findByText('Analysis complete! Loading report...')).toBeInTheDocument();

    // Advance 500ms delay for navigation
    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });

    expect(mockNavigate).toHaveBeenCalledWith('/report/test-run-123');
  });

  it('handles failed run status and displays error message with Try Again option', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ run_id: 'fail-run-456', status: 'pending' }),
    });

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: 'failed', error: 'Docker execution timeout' }),
    });

    renderUploadPage();

    const originalInput = screen.getByTestId('original-file-input');
    const migratedInput = screen.getByTestId('migrated-file-input');

    fireEvent.change(originalInput, { target: { files: [new File([''], 'o.zip')] } });
    fireEvent.change(migratedInput, { target: { files: [new File([''], 'm.zip')] } });

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Analyze Migration/i }));
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
    });

    expect(await screen.findByText('Docker execution timeout')).toBeInTheDocument();

    // Try Again reset
    const tryAgainBtn = screen.getByRole('button', { name: /Try Again/i });
    fireEvent.click(tryAgainBtn);

    expect(screen.queryByText('Docker execution timeout')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Analyze Migration/i })).toBeDisabled();
  });

  it('handles upload server error (non-2xx response)', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ detail: 'Invalid ZIP file format' }),
    });

    renderUploadPage();

    fireEvent.change(screen.getByTestId('original-file-input'), { target: { files: [new File([''], 'o.zip')] } });
    fireEvent.change(screen.getByTestId('migrated-file-input'), { target: { files: [new File([''], 'm.zip')] } });

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Analyze Migration/i }));
    });

    expect(await screen.findByText('Invalid ZIP file format')).toBeInTheDocument();
  });

  it('cleans up polling interval on unmount', async () => {
    const clearIntervalSpy = vi.spyOn(global, 'clearInterval');

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ run_id: 'cleanup-run-789', status: 'pending' }),
    });

    const { unmount } = renderUploadPage();

    fireEvent.change(screen.getByTestId('original-file-input'), { target: { files: [new File([''], 'o.zip')] } });
    fireEvent.change(screen.getByTestId('migrated-file-input'), { target: { files: [new File([''], 'm.zip')] } });

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Analyze Migration/i }));
    });

    unmount();

    expect(clearIntervalSpy).toHaveBeenCalled();
  });
});
