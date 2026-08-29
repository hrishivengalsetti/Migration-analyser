import { describe, it, expect, vi, beforeEach } from 'vitest';
import { uploadRun, getRunStatus, getReport } from '../client';

describe('api/client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  describe('uploadRun', () => {
    it('throws error when files are missing or not zip', async () => {
      await expect(uploadRun(null, null)).rejects.toThrow('Both original and migrated codebase ZIP files are required.');
      
      const txt = new File([''], 'a.txt');
      const zip = new File([''], 'b.zip');
      await expect(uploadRun(txt, zip)).rejects.toThrow('Both files must be .zip archives.');
    });

    it('handles non-2xx response with detail json', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Corrupted zip' }),
      });

      const z1 = new File([''], '1.zip');
      const z2 = new File([''], '2.zip');
      await expect(uploadRun(z1, z2)).rejects.toThrow('Corrupted zip');
    });

    it('handles network error', async () => {
      global.fetch.mockRejectedValueOnce(new TypeError('Failed to fetch'));

      const z1 = new File([''], '1.zip');
      const z2 = new File([''], '2.zip');
      await expect(uploadRun(z1, z2)).rejects.toThrow('Network error: Unable to connect to the backend server.');
    });
  });

  describe('getRunStatus', () => {
    it('throws error when runId is missing', async () => {
      await expect(getRunStatus(null)).rejects.toThrow('Run ID is required.');
    });

    it('handles non-2xx status error', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Run not found' }),
      });

      await expect(getRunStatus('invalid-id')).rejects.toThrow('Run not found');
    });

    it('handles network failure during polling', async () => {
      global.fetch.mockRejectedValueOnce(new TypeError('Failed to fetch'));

      await expect(getRunStatus('run-123')).rejects.toThrow('Network error: Server lost connection during polling.');
    });
  });

  describe('getReport', () => {
    it('throws error when runId is missing', async () => {
      await expect(getReport(null)).rejects.toThrow('Run ID is required.');
    });

    it('fetches report successfully', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: '123', classification: 'verified' }),
      });

      const data = await getReport('123');
      expect(data).toEqual({ run_id: '123', classification: 'verified' });
      expect(global.fetch).toHaveBeenCalledWith('/api/runs/123/report');
    });

    it('handles non-2xx report error', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Report not generated yet' }),
      });

      await expect(getReport('123')).rejects.toThrow('Report not generated yet');
    });
  });
});
