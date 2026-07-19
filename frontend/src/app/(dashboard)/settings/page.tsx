'use client'

import { PageHeader } from '@/components/shared/PageHeader'

export default function SettingsPage() {
  return (
    <div>
      <PageHeader
        title="Settings"
        subtitle="Manage your account preferences"
      />
      <div className="finora-card p-6 max-w-2xl">
        <h3 className="font-display font-bold text-lg mb-6">Profile Settings</h3>
        <p className="text-on-surface-variant">Settings form goes here</p>
      </div>
    </div>
  )
}
