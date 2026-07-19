'use client'

import { useState } from 'react'
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  SortingState,
  useReactTable,
} from '@tanstack/react-table'
import { EmptyState } from './EmptyState'
import { LoadingSpinner } from './LoadingSpinner'
import { cn } from '@/lib/utils'

interface DataTableProps<TData> {
  data: TData[]
  columns: ColumnDef<TData, any>[]
  loading?: boolean
  pagination?: {
    page: number
    perPage: number
    total: number
    onPageChange: (page: number) => void
  }
  onRowClick?: (row: TData) => void
  emptyMessage?: string
  searchable?: boolean
  onSearch?: (query: string) => void
}

export function DataTable<TData>({
  data,
  columns,
  loading = false,
  pagination,
  onRowClick,
  emptyMessage = 'No data found',
  searchable,
  onSearch,
}: DataTableProps<TData>) {
  const [sorting, setSorting] = useState<SortingState>([])
  const [searchQuery, setSearchQuery] = useState('')

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    onSortingChange: setSorting,
    getSortedRowModel: getSortedRowModel(),
    state: {
      sorting,
    },
  })

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value
    setSearchQuery(val)
    if (onSearch) onSearch(val)
  }

  return (
    <div className="finora-card overflow-hidden">
      {searchable && (
        <div className="p-4 border-b border-outline-variant flex items-center justify-between bg-surface-container-lowest">
          <div className="relative w-full max-w-sm">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[20px]">
              search
            </span>
            <input
              type="text"
              placeholder="Search..."
              value={searchQuery}
              onChange={handleSearch}
              className="w-full pl-10 pr-4 py-2 bg-surface-variant/30 border border-outline-variant rounded-lg text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors"
            />
          </div>
        </div>
      )}

      <div className="overflow-x-auto custom-scrollbar">
        <table className="w-full text-left border-collapse">
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id} className="bg-surface-variant/30 border-b border-outline-variant">
                {headerGroup.headers.map((header) => {
                  return (
                    <th
                      key={header.id}
                      colSpan={header.colSpan}
                      className="px-6 py-3 text-xs font-semibold text-on-surface-variant uppercase tracking-wider whitespace-nowrap"
                    >
                      {header.isPlaceholder ? null : (
                        <div
                          {...{
                            className: header.column.getCanSort()
                              ? 'cursor-pointer select-none flex items-center gap-1 hover:text-on-surface transition-colors'
                              : '',
                            onClick: header.column.getToggleSortingHandler(),
                          }}
                        >
                          {flexRender(header.column.columnDef.header, header.getContext())}
                          {{
                            asc: <span className="material-symbols-outlined text-[16px]">arrow_upward</span>,
                            desc: <span className="material-symbols-outlined text-[16px]">arrow_downward</span>,
                          }[header.column.getIsSorted() as string] ?? null}
                        </div>
                      )}
                    </th>
                  )
                })}
              </tr>
            ))}
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i} className="border-b border-outline-variant last:border-0">
                  {columns.map((_, j) => (
                    <td key={j} className="px-6 py-4">
                      <div className="h-4 bg-surface-variant rounded animate-pulse w-3/4"></div>
                    </td>
                  ))}
                </tr>
              ))
            ) : table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <tr
                  key={row.id}
                  onClick={() => onRowClick && onRowClick(row.original)}
                  className={cn(
                    "border-b border-outline-variant last:border-0 bg-surface-container-lowest transition-colors",
                    onRowClick && "cursor-pointer hover:bg-surface-variant/30"
                  )}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-6 py-4 text-sm text-on-surface whitespace-nowrap">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={columns.length} className="px-6 py-12 text-center text-on-surface-variant">
                  <EmptyState title={emptyMessage} icon="database" className="shadow-none border-none bg-transparent p-0" />
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {pagination && pagination.total > pagination.perPage && (
        <div className="px-6 py-4 border-t border-outline-variant flex items-center justify-between bg-surface-container-lowest">
          <div className="text-sm text-on-surface-variant">
            Showing <span className="font-medium text-on-surface">{(pagination.page - 1) * pagination.perPage + 1}</span> to{' '}
            <span className="font-medium text-on-surface">
              {Math.min(pagination.page * pagination.perPage, pagination.total)}
            </span>{' '}
            of <span className="font-medium text-on-surface">{pagination.total}</span> results
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => pagination.onPageChange(pagination.page - 1)}
              disabled={pagination.page === 1 || loading}
              className="px-3 py-1 text-sm border border-outline-variant rounded-md disabled:opacity-50 hover:bg-surface-variant transition-colors"
            >
              Previous
            </button>
            <button
              onClick={() => pagination.onPageChange(pagination.page + 1)}
              disabled={pagination.page * pagination.perPage >= pagination.total || loading}
              className="px-3 py-1 text-sm border border-outline-variant rounded-md disabled:opacity-50 hover:bg-surface-variant transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
