import type { ReactNode } from "react";

import { cn } from "../lib/utils";

export interface Column<T> {
  key: string;
  label: string;
  render: (item: T) => ReactNode;
  className?: string;
}

export function DataTable<T>({
  columns,
  rows,
  getRowKey,
  emptyText = "No data",
}: {
  columns: Column<T>[];
  rows: T[];
  getRowKey: (row: T) => string;
  emptyText?: string;
}) {
  return (
    <div className="overflow-hidden rounded-2xl border border-gray-100 bg-white">
      <table className="min-w-full divide-y divide-gray-100 text-left">
        <thead>
          <tr className="bg-gray-50">
            {columns.map((column) => (
              <th
                key={column.key}
                className={cn(
                  "px-4 py-3 text-[10px] font-semibold uppercase tracking-[0.28em] text-gray-400",
                  column.className,
                )}
              >
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {rows.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-4 py-8 text-center text-sm text-gray-400"
              >
                {emptyText}
              </td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr key={getRowKey(row)} className="text-sm text-gray-700 transition hover:bg-gray-50">
                {columns.map((column) => (
                  <td key={column.key} className="px-4 py-3">
                    {column.render(row)}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
