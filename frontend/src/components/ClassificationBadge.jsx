import React from 'react';

const CONFIG = {
  verified: {
    label: 'VERIFIED',
    bg: 'bg-green-100 text-green-800 border-green-300',
    icon: (
      <svg className="w-5 h-5 mr-1.5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
      </svg>
    ),
  },
  partially_verified: {
    label: 'PARTIALLY VERIFIED',
    bg: 'bg-amber-100 text-amber-800 border-amber-300',
    icon: (
      <svg className="w-5 h-5 mr-1.5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    ),
  },
  regression_detected: {
    label: 'REGRESSION DETECTED',
    bg: 'bg-red-100 text-red-800 border-red-300',
    icon: (
      <svg className="w-5 h-5 mr-1.5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
      </svg>
    ),
  },
  unverified: {
    label: 'UNVERIFIED',
    bg: 'bg-gray-100 text-gray-800 border-gray-300',
    icon: (
      <svg className="w-5 h-5 mr-1.5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
};

export default function ClassificationBadge({ classification }) {
  const normKey = (classification || '').toLowerCase();
  const item = CONFIG[normKey] || CONFIG.unverified;

  return (
    <div
      data-testid="classification-badge"
      className={`inline-flex items-center px-4 py-2 rounded-full border text-sm font-bold shadow-sm ${item.bg}`}
    >
      {item.icon}
      <span>{item.label}</span>
    </div>
  );
}
