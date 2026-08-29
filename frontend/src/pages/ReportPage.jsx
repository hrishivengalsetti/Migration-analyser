import React from 'react';
import { useParams } from 'react-router-dom';

export default function ReportPage() {
  const { runId } = useParams();

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold">Report Page</h1>
      <p className="text-gray-600 mt-2">Run ID: {runId}</p>
    </div>
  );
}
