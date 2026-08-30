import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import FileUploader from '../components/FileUploader';
import StatusProgress from '../components/StatusProgress';
import { uploadRun, getRunStatus } from '../api/client';

export default function UploadPage() {
  const [originalFile, setOriginalFile] = useState(null);
  const [migratedFile, setMigratedFile] = useState(null);
  const [status, setStatus] = useState(null);
  const [runId, setRunId] = useState(null);
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const navigate = useNavigate();

  // Polling logic with 1000ms interval
  useEffect(() => {
    if (!runId || status === 'complete' || status === 'failed') return;

    let active = true;

    const interval = setInterval(async () => {
      try {
        const data = await getRunStatus(runId);
        if (!active) return;

        setStatus(data.status);

        if (data.status === 'failed') {
          setError(data.error || 'Pipeline execution failed.');
        } else if (data.status === 'complete') {
          setTimeout(() => {
            navigate(`/report/${runId}`);
          }, 500);
        }
      } catch (err) {
        if (!active) return;
        setStatus('failed');
        setError(err.message || 'Error occurred while polling status.');
      }
    }, 1000);

    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [runId, status, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!originalFile || !migratedFile) {
      setError('Both original and migrated codebase ZIP files are required.');
      return;
    }

    setIsSubmitting(true);
    setError(null);
    setStatus('pending');

    try {
      const data = await uploadRun(originalFile, migratedFile);
      setRunId(data.run_id);
      setStatus(data.status || 'pending');
    } catch (err) {
      setIsSubmitting(false);
      setStatus('failed');
      setError(err.message || 'Failed to trigger migration analysis.');
    }
  };

  const handleReset = () => {
    setOriginalFile(null);
    setMigratedFile(null);
    setStatus(null);
    setRunId(null);
    setError(null);
    setIsSubmitting(false);
  };

  const isSubmitDisabled = !originalFile || !migratedFile || isSubmitting;

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl w-full mx-auto space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">
            Migration Verifier
          </h1>
          <p className="mt-2 text-sm text-gray-600">
            Upload original and migrated Python codebase zips to analyze diffs, compute blast radius, and run sandboxed behavioral verification.
          </p>
        </div>

        <div className="bg-white py-8 px-6 shadow rounded-lg sm:px-10 border border-gray-100">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
              <FileUploader
                id="original-file-input"
                label="Original Codebase (.zip)"
                selectedFile={originalFile}
                onFileSelect={setOriginalFile}
              />
              <FileUploader
                id="migrated-file-input"
                label="Migrated Codebase (.zip)"
                selectedFile={migratedFile}
                onFileSelect={setMigratedFile}
              />
            </div>

            {!status && (
              <div>
                <button
                  type="submit"
                  disabled={isSubmitDisabled}
                  className={`w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white transition-colors ${
                    isSubmitDisabled
                      ? 'bg-gray-300 cursor-not-allowed'
                      : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'
                  }`}
                >
                  {isSubmitting ? 'Uploading...' : 'Analyze Migration'}
                </button>
              </div>
            )}
          </form>

          {status && <StatusProgress status={status} error={error} />}

          {status === 'failed' && (
            <div className="mt-4 text-center">
              <button
                onClick={handleReset}
                className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Try Again
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
