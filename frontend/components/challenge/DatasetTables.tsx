interface DatasetTable {
  name: string;
  columns: string[];
  rows: unknown[][];
}

function isDatasetTable(value: unknown): value is DatasetTable {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.name === "string" &&
    Array.isArray(candidate.columns) &&
    Array.isArray(candidate.rows)
  );
}

/**
 * Challenge.dataset is typed `unknown` on purpose (the sandbox interprets
 * its shape, not the UI) — this renders it as real tables when it matches
 * the expected SandboxDataset shape, and falls back to raw JSON otherwise
 * rather than crashing on an unexpected shape.
 */
export function DatasetTables({ dataset }: { dataset: unknown }) {
  const tables = (dataset as { tables?: unknown[] } | null)?.tables;

  if (!Array.isArray(tables) || tables.length === 0 || !tables.every(isDatasetTable)) {
    return (
      <pre className="overflow-x-auto rounded-md bg-slate-900 p-3 text-xs text-slate-100">
        {JSON.stringify(dataset, null, 2)}
      </pre>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {tables.map((table) => (
        <div key={table.name} className="overflow-x-auto rounded-md border border-slate-200">
          <div className="border-b border-slate-200 bg-slate-50 px-3 py-1.5 font-mono text-xs font-medium text-slate-600">
            {table.name}
          </div>
          <table className="w-full border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 text-left text-slate-500">
                {table.columns.map((col) => (
                  <th key={col} className="border-b border-slate-200 px-3 py-1.5 font-mono">
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {table.rows.map((row, rowIndex) => (
                <tr key={rowIndex} className="border-b border-slate-100 last:border-0">
                  {row.map((cell, cellIndex) => (
                    <td key={cellIndex} className="px-3 py-1.5 font-mono">
                      {cell === null ? <span className="italic text-slate-400">NULL</span> : String(cell)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}
