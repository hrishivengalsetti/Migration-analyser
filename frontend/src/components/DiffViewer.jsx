import React from 'react';

export default function DiffViewer({ originalContent = '', migratedContent = '' }) {
  const origLines = (originalContent || '').split('\n');
  const migLines = (migratedContent || '').split('\n');

  // Compute basic line diff
  const maxLines = Math.max(origLines.length, migLines.length);
  const rows = [];

  for (let i = 0; i < maxLines; i++) {
    const orig = origLines[i];
    const mig = migLines[i];

    if (orig === mig) {
      rows.push({ type: 'unchanged', origNum: i + 1, migNum: i + 1, origText: orig, migText: mig });
    } else {
      if (orig !== undefined) {
        rows.push({ type: 'removed', origNum: i + 1, migNum: null, origText: orig, migText: '' });
      }
      if (mig !== undefined) {
        rows.push({ type: 'added', origNum: null, migNum: i + 1, origText: '', migText: mig });
      }
    }
  }

  return (
    <div className="border border-gray-200 rounded-md overflow-hidden font-mono text-xs bg-gray-900 text-gray-100 my-2">
      <div className="grid grid-cols-2 bg-gray-800 px-4 py-1.5 text-gray-400 border-b border-gray-700 font-semibold">
        <div>Original Source</div>
        <div>Migrated Source</div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <tbody>
            {rows.map((row, idx) => (
              <tr
                key={idx}
                className={
                  row.type === 'removed'
                    ? 'bg-red-950/60 text-red-200'
                    : row.type === 'added'
                    ? 'bg-green-950/60 text-green-200'
                    : 'hover:bg-gray-800/40 text-gray-300'
                }
              >
                <td className="w-10 select-none text-right pr-2 py-0.5 text-gray-600 border-r border-gray-800">
                  {row.origNum || ''}
                </td>
                <td className="w-1/2 px-3 py-0.5 whitespace-pre border-r border-gray-800">
                  {row.type === 'removed' && <span className="text-red-400 font-bold mr-1">-</span>}
                  {row.origText}
                </td>
                <td className="w-10 select-none text-right pr-2 py-0.5 text-gray-600 border-r border-gray-800">
                  {row.migNum || ''}
                </td>
                <td className="w-1/2 px-3 py-0.5 whitespace-pre">
                  {row.type === 'added' && <span className="text-green-400 font-bold mr-1">+</span>}
                  {row.migText}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
