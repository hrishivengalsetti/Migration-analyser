import React from 'react';

export default function TestResults({ testResults = [] }) {
  if (!testResults || testResults.length === 0) {
    return (
      <div className="bg-white p-12 rounded-lg border border-gray-200 shadow-sm text-center" data-testid="test-results-empty">
        <h3 className="text-lg font-bold text-gray-700 mb-2">No Tests Executed</h3>
        <p className="text-sm text-gray-500">No tests were executed for this migration.</p>
      </div>
    );
  }

  // Calculate summary counts
  const total = testResults.length;
  const regressions = testResults.filter((t) => t.comparison === 'regression').length;
  const passedBoth = testResults.filter(
    (t) => t.comparison === 'passed_both' || (t.status_original === 'passed' && t.status_migrated === 'passed')
  ).length;

  // Sort by test_id
  const sortedTests = [...testResults].sort((a, b) => (a.test_id || '').localeCompare(b.test_id || ''));

  return (
    <div className="space-y-6" data-testid="test-results-component">
      {/* Summary Header */}
      <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm flex items-center justify-between text-sm">
        <div className="font-semibold text-gray-700">
          Execution Summary: <span className="text-gray-900 font-bold">{total} Total Tests</span>
        </div>
        <div className="flex items-center space-x-4 font-medium">
          <span className="text-green-700 bg-green-50 px-2.5 py-1 rounded-md border border-green-200">
            {passedBoth} Passed
          </span>
          <span
            className={`px-2.5 py-1 rounded-md border ${
              regressions > 0
                ? 'text-red-700 bg-red-50 border-red-200 font-bold'
                : 'text-gray-600 bg-gray-50 border-gray-200'
            }`}
          >
            {regressions} Regressions
          </span>
        </div>
      </div>

      {/* Tests Table */}
      <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50 text-gray-500 font-semibold text-xs uppercase tracking-wider">
              <tr>
                <th scope="col" className="px-6 py-3 text-left">
                  Test Name
                </th>
                <th scope="col" className="px-6 py-3 text-center">
                  Original Status
                </th>
                <th scope="col" className="px-6 py-3 text-center">
                  Migrated Status
                </th>
                <th scope="col" className="px-6 py-3 text-center">
                  Result
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sortedTests.map((t, idx) => {
                const isRegression = t.comparison === 'regression';

                const origBadgeColor =
                  t.status_original === 'passed'
                    ? 'bg-green-100 text-green-800'
                    : t.status_original === 'failed'
                    ? 'bg-red-100 text-red-800'
                    : 'bg-gray-100 text-gray-700';

                const migBadgeColor =
                  t.status_migrated === 'passed'
                    ? 'bg-green-100 text-green-800'
                    : t.status_migrated === 'failed'
                    ? 'bg-red-100 text-red-800'
                    : 'bg-gray-100 text-gray-700';

                const compBadgeColor =
                  t.comparison === 'regression'
                    ? 'bg-red-100 text-red-800 border-red-300'
                    : t.comparison === 'passed_both' || t.comparison === 'passed'
                    ? 'bg-green-100 text-green-800 border-green-300'
                    : t.comparison === 'improvement' || t.comparison === 'improved'
                    ? 'bg-blue-100 text-blue-800 border-blue-300'
                    : 'bg-gray-100 text-gray-800 border-gray-300';

                return (
                  <tr
                    key={t.test_id || idx}
                    className={isRegression ? 'bg-red-50/70 hover:bg-red-100/50' : 'hover:bg-gray-50'}
                    data-testid={`test-row-${idx}`}
                  >
                    <td className="px-6 py-4 font-mono text-xs text-gray-900 break-all font-medium">
                      {t.test_id}
                    </td>
                    <td className="px-6 py-4 text-center whitespace-nowrap">
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase ${origBadgeColor}`}>
                        {t.status_original || 'N/A'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center whitespace-nowrap">
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase ${migBadgeColor}`}>
                        {t.status_migrated || 'N/A'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center whitespace-nowrap">
                      <span
                        className={`px-3 py-1 rounded-full border text-xs font-bold uppercase ${compBadgeColor}`}
                        data-testid={`test-comparison-${idx}`}
                      >
                        {t.comparison}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
