import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import ClassificationBadge from '../components/ClassificationBadge';
import DiffViewer from '../components/DiffViewer';
import { getReport } from '../api/client';

export default function ReportPage() {
  const { runId } = useParams();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('summary');
  const [expandedFiles, setExpandedFiles] = useState({});
  const [expandedSymbols, setExpandedSymbols] = useState({});

  useEffect(() => {
    async function loadReport() {
      try {
        setLoading(true);
        setError(null);
        const data = await getReport(runId);
        setReport(data);
      } catch (err) {
        setError(err.message || 'Failed to load report.');
      } finally {
        setLoading(false);
      }
    }

    if (runId) {
      loadReport();
    }
  }, [runId]);

  const toggleFile = (filePath) => {
    setExpandedFiles((prev) => ({ ...prev, [filePath]: !prev[filePath] }));
  };

  const toggleSymbol = (symId) => {
    setExpandedSymbols((prev) => ({ ...prev, [symId]: !prev[symId] }));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 text-sm font-medium">Loading analysis report...</p>
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-3xl mx-auto bg-white p-6 rounded-lg border border-red-200 shadow-sm text-center">
          <h2 className="text-xl font-bold text-red-800 mb-2">Unable to Load Report</h2>
          <p className="text-gray-600 mb-6">{error || 'Report data not found.'}</p>
          <Link
            to="/"
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
          >
            Return to Upload
          </Link>
        </div>
      </div>
    );
  }

  const summary = report.summary || {};
  const fileDiffs = report.file_diffs || [];
  const symbolDiffs = report.symbol_diffs || [];

  return (
    <div className="min-h-screen bg-gray-50 pb-12">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Link to="/" className="text-gray-500 hover:text-gray-700 text-sm font-medium">
              &larr; Upload New Migration
            </Link>
            <span className="text-gray-300">|</span>
            <h1 className="text-xl font-bold text-gray-900">Migration Analysis Report</h1>
          </div>
          <div className="text-xs text-gray-500 font-mono">
            Run ID: <span className="font-semibold text-gray-700">{report.run_id || runId}</span>
          </div>
        </div>

        {/* Horizontal Navigation Tabs */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="-mb-px flex space-x-8" aria-label="Tabs">
            {[
              { id: 'summary', name: 'Summary' },
              { id: 'changes', name: `Changes (${fileDiffs.length})` },
              { id: 'impact', name: 'Impact Graph' },
              { id: 'tests', name: 'Test Results' },
              { id: 'evidence', name: 'Evidence' },
            ].map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    isActive
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {tab.name}
                </button>
              );
            })}
          </nav>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
        {/* SUMMARY TAB */}
        {activeTab === 'summary' && (
          <div className="space-y-8">
            {/* Top Banner Card */}
            <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
              <div>
                <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider block mb-1">
                  Overall Verification Result
                </span>
                <ClassificationBadge classification={report.classification} />
              </div>
              <div className="text-right text-sm text-gray-500">
                Created: {report.created_at ? new Date(report.created_at).toLocaleString() : 'N/A'}
              </div>
            </div>

            {/* Metrics Card Grid */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-sm text-center">
                <p className="text-3xl font-extrabold text-gray-900" data-testid="files-changed">
                  {summary.total_files_changed}
                </p>
                <p className="text-xs font-medium text-gray-500 mt-1">Files Changed</p>
              </div>

              <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-sm text-center">
                <p className="text-3xl font-extrabold text-gray-900" data-testid="symbols-changed">
                  {summary.total_symbols_changed}
                </p>
                <p className="text-xs font-medium text-gray-500 mt-1">Symbols Changed</p>
              </div>

              <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-sm text-center">
                <p className="text-3xl font-extrabold text-blue-600" data-testid="blast-radius">
                  {summary.total_affected_symbols}
                </p>
                <p className="text-xs font-medium text-gray-500 mt-1">Blast Radius</p>
              </div>

              <div
                className={`bg-white p-5 rounded-lg border shadow-sm text-center ${
                  summary.regressions_count > 0 ? 'border-red-300 bg-red-50/50' : 'border-gray-200'
                }`}
              >
                <p
                  className={`text-3xl font-extrabold ${
                    summary.regressions_count > 0 ? 'text-red-600' : 'text-gray-900'
                  }`}
                  data-testid="regressions"
                >
                  {summary.regressions_count}
                </p>
                <p className="text-xs font-medium text-gray-500 mt-1">Regressions</p>
              </div>

              <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-sm text-center">
                <p className="text-3xl font-extrabold text-gray-900" data-testid="tests-run">
                  {summary.total_tests_run}
                </p>
                <p className="text-xs font-medium text-gray-500 mt-1">Tests Run</p>
              </div>
            </div>
          </div>
        )}

        {/* CHANGES TAB */}
        {activeTab === 'changes' && (
          <div className="space-y-8">
            {/* File Level Diffs */}
            <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
              <h3 className="text-lg font-bold text-gray-900 mb-4">
                File Diffs ({fileDiffs.length})
              </h3>
              {fileDiffs.length === 0 ? (
                <p className="text-sm text-gray-500">No file diffs recorded.</p>
              ) : (
                <div className="space-y-3">
                  {fileDiffs.map((fd, idx) => {
                    const isExpanded = !!expandedFiles[fd.file || idx];
                    const statusColor =
                      fd.status === 'added'
                        ? 'bg-green-100 text-green-800'
                        : fd.status === 'deleted'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-yellow-100 text-yellow-800';

                    return (
                      <div key={idx} className="border border-gray-200 rounded-md overflow-hidden">
                        <button
                          onClick={() => toggleFile(fd.file || idx)}
                          className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 text-left transition-colors"
                        >
                          <div className="flex items-center space-x-3">
                            <span className="font-mono text-sm font-semibold text-gray-800">
                              {fd.file}
                            </span>
                            <span
                              className={`text-xs px-2 py-0.5 rounded font-semibold uppercase ${statusColor}`}
                            >
                              {fd.status}
                            </span>
                          </div>
                          <span className="text-xs text-blue-600 font-medium">
                            {isExpanded ? 'Hide Diff ▲' : 'Show Diff ▼'}
                          </span>
                        </button>

                        {isExpanded && (
                          <div className="p-3 bg-white border-t border-gray-200">
                            <DiffViewer
                              originalContent={fd.original_content}
                              migratedContent={fd.migrated_content}
                            />
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Symbol Level Diffs */}
            <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
              <h3 className="text-lg font-bold text-gray-900 mb-4">
                AST Symbol Diffs ({symbolDiffs.length})
              </h3>
              {symbolDiffs.length === 0 ? (
                <p className="text-sm text-gray-500">No symbol-level AST diffs detected.</p>
              ) : (
                <div className="space-y-3">
                  {symbolDiffs.map((sd, idx) => {
                    const isExpanded = !!expandedSymbols[sd.symbol_id || idx];
                    return (
                      <div key={idx} className="border border-gray-200 rounded-md overflow-hidden">
                        <button
                          onClick={() => toggleSymbol(sd.symbol_id || idx)}
                          className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 text-left transition-colors"
                        >
                          <div className="flex items-center space-x-3">
                            <span className="font-mono text-sm font-semibold text-blue-700">
                              {sd.symbol_id}
                            </span>
                            <span className="text-xs px-2 py-0.5 rounded bg-gray-200 text-gray-700 font-semibold uppercase">
                              {sd.kind}
                            </span>
                            <span className="text-xs px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-semibold">
                              {sd.change_kind}
                            </span>
                          </div>
                          <span className="text-xs text-blue-600 font-medium">
                            {isExpanded ? 'Hide Source ▲' : 'Show Source ▼'}
                          </span>
                        </button>

                        {isExpanded && (
                          <div className="p-3 bg-white border-t border-gray-200">
                            <div className="text-xs text-gray-500 mb-2">
                              File: <span className="font-mono text-gray-700">{sd.file}</span> | Lines: {sd.line_original ?? 'N/A'} &rarr; {sd.line_migrated ?? 'N/A'}
                            </div>
                            <DiffViewer
                              originalContent={sd.original_source}
                              migratedContent={sd.migrated_source}
                            />
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        )}

        {/* PLACEHOLDER TABS */}
        {['impact', 'tests', 'evidence'].includes(activeTab) && (
          <div className="bg-white p-12 rounded-lg border border-gray-200 shadow-sm text-center">
            <h3 className="text-lg font-bold text-gray-700 mb-2 capitalize">{activeTab} View</h3>
            <p className="text-sm text-gray-500">Coming soon in upcoming tasks.</p>
          </div>
        )}
      </main>
    </div>
  );
}
