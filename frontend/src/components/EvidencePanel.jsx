import React from 'react';

const COMPARISON_BADGES = {
  verified: {
    label: '✓ Verified',
    style: 'bg-green-100 text-green-800 border-green-300',
  },
  regression: {
    label: '✗ Regression',
    style: 'bg-red-100 text-red-800 border-red-300',
  },
  improved: {
    label: '↑ Improved',
    style: 'bg-blue-100 text-blue-800 border-blue-300',
  },
  no_tests: {
    label: '? No Tests',
    style: 'bg-gray-100 text-gray-700 border-gray-300',
  },
};

export default function EvidencePanel({ evidence = [] }) {
  if (!evidence || evidence.length === 0) {
    return (
      <div className="bg-white p-12 rounded-lg border border-gray-200 shadow-sm text-center" data-testid="evidence-empty">
        <h3 className="text-lg font-bold text-gray-700 mb-2">No Evidence Available</h3>
        <p className="text-sm text-gray-500">No symbol changes detected in this migration.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="evidence-panel-component">
      {evidence.map((item, idx) => {
        const isRegression = item.comparison === 'regression';
        const badgeConfig = COMPARISON_BADGES[item.comparison] || COMPARISON_BADGES.no_tests;

        const passing = item.passing_tests || [];
        const failing = item.failing_tests || [];

        return (
          <div
            key={item.symbol_id || idx}
            data-testid={`evidence-card-${idx}`}
            className={`bg-white p-6 rounded-lg border shadow-sm transition-shadow ${
              isRegression ? 'border-red-400 bg-red-50/20 shadow-red-100' : 'border-gray-200'
            }`}
          >
            {/* Card Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-gray-100 pb-3 mb-4">
              <div>
                <span className="font-mono text-base font-bold text-blue-800 break-all block">
                  {item.symbol_id}
                </span>
                <span className="text-xs text-gray-500 font-mono">File: {item.file}</span>
              </div>
              <div className="flex items-center space-x-2">
                {item.change_kind && (
                  <span className="text-xs px-2.5 py-0.5 rounded bg-amber-100 text-amber-800 font-semibold uppercase">
                    {item.change_kind}
                  </span>
                )}
                <span
                  className={`text-xs px-3 py-1 rounded-full border font-bold ${badgeConfig.style}`}
                  data-testid={`evidence-badge-${idx}`}
                >
                  {badgeConfig.label}
                </span>
              </div>
            </div>

            {/* Test Results Sections */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              {/* Passing Tests */}
              <div className="bg-gray-50 p-3 rounded-md border border-gray-200">
                <span className="font-semibold text-green-700 block mb-1">
                  Passing Tests ({passing.length})
                </span>
                {passing.length === 0 ? (
                  <p className="text-gray-400 italic">None</p>
                ) : (
                  <ul className="list-disc list-inside font-mono text-gray-700 space-y-1">
                    {passing.map((t, tIdx) => (
                      <li key={tIdx} className="break-all">
                        {t}
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Failing Tests */}
              <div className="bg-gray-50 p-3 rounded-md border border-gray-200">
                <span className="font-semibold text-red-700 block mb-1">
                  Failing Tests ({failing.length})
                </span>
                {failing.length === 0 ? (
                  <p className="text-gray-400 italic">None</p>
                ) : (
                  <ul className="list-disc list-inside font-mono text-red-800 space-y-1">
                    {failing.map((t, tIdx) => (
                      <li key={tIdx} className="break-all font-semibold">
                        {t}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
