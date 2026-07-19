'use client'

import { PageHeader } from '@/components/shared/PageHeader'
import { EmptyState } from '@/components/shared/EmptyState'

export default function ReportsPage() {
  return (
    <div>
      <PageHeader
        title="Reports"
        subtitle="Generate and download financial reports"
      />
      <EmptyState
        title="Reports coming soon"
        description="We are working on adding comprehensive reports to Finora."
        icon="analytics"
      />
    </div>
  )
}
