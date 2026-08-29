import React from 'react';

export default function AINarrative({ interpretation }) {
  if (!interpretation) {
    return (
      <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm text-center" data-testid="ai-narrative-empty">
        <p className="text-sm text-gray-500">AI analysis is not available for this run.</p>
      </div>
    );
  }

  const { migration_intent, risk_summary, key_concerns = [], confidence } = interpretation;

  const confColor =
    confidence === 'high'
      ? 'bg-green-100 text-green-800 border-green-300'
      : confidence === 'medium'
      ? 'bg-amber-100 text-amber-800 border-amber-300'
      : 'bg-gray-100 text-gray-800 border-gray-300';

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm space-y-4" data-testid="ai-narrative-component">
      <div className="flex items-center justify-between border-b border-gray-100 pb-3">
        <div className="flex items-center space-x-2">
          <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 10V3L4 14h7v7l9-11h-7z"
            />
          </svg>
          <h3 className="text-lg font-bold text-gray-900">AI-Generated Narrative</h3>
        </div>
        {confidence && (
          <span className={`text-xs px-2.5 py-0.5 rounded-full border font-bold uppercase ${confColor}`}>
            Confidence: {confidence}
          </span>
        )}
      </div>

      <div>
        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider block">
          Migration Intent
        </span>
        <p className="text-sm text-gray-800 mt-1">{migration_intent || 'N/A'}</p>
      </div>

      <div>
        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider block">
          Risk Summary
        </span>
        <p className="text-sm text-gray-800 mt-1">{risk_summary || 'N/A'}</p>
      </div>

      {key_concerns && key_concerns.length > 0 && (
        <div>
          <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider block mb-1">
            Key Concerns
          </span>
          <ul className="list-disc list-inside text-sm text-gray-800 space-y-1">
            {key_concerns.map((concern, idx) => (
              <li key={idx}>{concern}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="text-[11px] text-gray-400 italic pt-2 border-t border-gray-100">
        Note: AI narrative is generated for interpretation purposes only. Verification status and evidence remain strictly deterministic.
      </div>
    </div>
  );
}
