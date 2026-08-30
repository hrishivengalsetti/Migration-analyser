import React from 'react';

const STATUS_MAP = {
  pending: { progress: 10, label: 'Initializing run...', color: 'bg-gray-400' },
  analyzing: { progress: 30, label: 'Analyzing AST diffs & call graph...', color: 'bg-blue-600' },
  executing: { progress: 60, label: 'Executing sandboxed tests in Docker...', color: 'bg-blue-600' },
  interpreting: { progress: 85, label: 'Generating AI narrative interpretation...', color: 'bg-blue-600' },
  complete: { progress: 100, label: 'Analysis complete! Loading report...', color: 'bg-green-600' },
  failed: { progress: 100, label: 'Pipeline execution failed.', color: 'bg-red-600' },
};

export default function StatusProgress({ status, error }) {
  if (!status) return null;

  const current = STATUS_MAP[status] || {
    progress: 5,
    label: status,
    color: 'bg-blue-600',
  };

  return (
    <div className="w-full mt-6 bg-white p-6 rounded-lg border border-gray-200 shadow-sm" data-testid="status-progress">
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm font-medium text-gray-700">{current.label}</span>
        <span className="text-sm font-semibold text-gray-900">{current.progress}%</span>
      </div>

      <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
        <div
          className={`h-3 rounded-full transition-all duration-500 ease-out ${current.color}`}
          style={{ width: `${current.progress}%` }}
        />
      </div>

      {status === 'failed' && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md" data-testid="error-banner">
          <div className="flex items-start">
            <svg
              className="h-5 w-5 text-red-500 mr-2 mt-0.5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <div>
              <h4 className="text-sm font-semibold text-red-800">Execution Error</h4>
              <p className="text-sm text-red-700 mt-1">{error || 'An unexpected error occurred during pipeline execution.'}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
