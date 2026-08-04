'use client'

import { useState, useEffect } from 'react'
import { PageHeader } from '@/components/shared/PageHeader'
import { authApi, settingsApi } from '@/lib/api'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { BackupRestoreModal } from '@/components/features/settings/BackupRestoreModal'
import { GoogleOAuthProvider } from '@react-oauth/google'

export default function SettingsPage() {
  const queryClient = useQueryClient()
  
  // Local state for UI
  const [theme, setTheme] = useState<'Light' | 'Dark' | 'Auto'>('Light')
  const [compactMode, setCompactMode] = useState(false)
  const [currency, setCurrency] = useState('INR')

  // Modals state
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false)
  const [isPasswordModalOpen, setIsPasswordModalOpen] = useState(false)
  const [isCategoryModalOpen, setIsCategoryModalOpen] = useState(false)
  const [isBackupModalOpen, setIsBackupModalOpen] = useState(false)

  // Forms state
  const [profileForm, setProfileForm] = useState({ full_name: '', phone: '' })
  const [passwordForm, setPasswordForm] = useState({ current_password: '', new_password: '' })
  const [categoryForm, setCategoryForm] = useState({ name: '', type: 'expense', color: '#795548', icon: 'category' })

  // Data fetching
  const { data: userRes } = useQuery({
    queryKey: ['user-me'],
    queryFn: () => authApi.me().then(r => r.data),
  })

  const { data: categoriesRes } = useQuery({
    queryKey: ['settings-categories'],
    queryFn: () => settingsApi.getCategories().then(r => r.data),
  })

  const user = userRes?.data
  const categories = categoriesRes?.data || []

  // Initialize local state from user data
  useEffect(() => {
    if (user) {
      setTheme((user.theme === 'dark' ? 'Dark' : user.theme === 'auto' ? 'Auto' : 'Light'))
      setCurrency(user.currency || 'INR')
      setProfileForm({ full_name: user.full_name || '', phone: user.phone || '' })
    }
  }, [user])

  // Mutations
  const updateProfileMutation = useMutation({
    mutationFn: (data: any) => settingsApi.updateProfile(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-me'] })
      setIsProfileModalOpen(false)
      alert('Profile updated successfully!')
    }
  })

  const changePasswordMutation = useMutation({
    mutationFn: (data: any) => settingsApi.changePassword(data),
    onSuccess: () => {
      alert('Password updated successfully!')
      setIsPasswordModalOpen(false)
      setPasswordForm({ current_password: '', new_password: '' })
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || 'Failed to change password')
    }
  })

  const createCategoryMutation = useMutation({
    mutationFn: (data: any) => settingsApi.createCategory(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings-categories'] })
      setIsCategoryModalOpen(false)
      setCategoryForm({ name: '', type: 'expense', color: '#795548', icon: 'category' })
    }
  })

  const resetDemoMutation = useMutation({
    mutationFn: () => settingsApi.resetDemo(),
    onSuccess: () => {
      alert('Account has been reset.')
      window.location.reload()
    }
  })

  // Handlers
  const handleUpdateProfile = (e: React.FormEvent) => {
    e.preventDefault()
    updateProfileMutation.mutate(profileForm)
  }

  const handleChangePassword = (e: React.FormEvent) => {
    e.preventDefault()
    changePasswordMutation.mutate(passwordForm)
  }

  const handleCreateCategory = (e: React.FormEvent) => {
    e.preventDefault()
    createCategoryMutation.mutate(categoryForm)
  }

  const handleSaveConfig = () => {
    updateProfileMutation.mutate({ 
      theme: theme.toLowerCase(),
      currency: currency
    })
  }

  const handleExportJSON = async () => {
    const pwd = window.prompt("Enter a strong password to encrypt your local backup:\n(You will need this password to restore it later)")
    if (!pwd) return
    try {
      const payload = await settingsApi.exportData()
      const encrypted = await encryptData(payload, pwd)
      const dataStr = "data:text/plain;charset=utf-8," + encodeURIComponent(encrypted)
      const downloadAnchorNode = document.createElement('a')
      downloadAnchorNode.setAttribute("href", dataStr)
      downloadAnchorNode.setAttribute("download", `finora-backup-local-${new Date().toISOString().replace(/[:.]/g, '-')}.enc`)
      document.body.appendChild(downloadAnchorNode)
      downloadAnchorNode.click()
      downloadAnchorNode.remove()
    } catch (e: any) {
      alert("Failed to export backup: " + e.message)
    }
  }

  const handleReset = () => {
    if (confirm("Are you sure you want to reset your account? This will delete all your data!")) {
      resetDemoMutation.mutate()
    }
  }

  const handleImportJSONClick = () => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.enc'
    input.onchange = async (e: any) => {
      if (e.target.files?.length > 0) {
        const file = e.target.files[0]
        const pwd = window.prompt("Enter the password to decrypt this backup file:")
        if (!pwd) return
        
        const reader = new FileReader()
        reader.onload = async (ev) => {
          try {
            const encryptedData = ev.target?.result as string
            const decryptedPayload = await decryptData(encryptedData, pwd)
            await settingsApi.restoreData(decryptedPayload)
            alert('Data successfully restored! The page will now reload.')
            window.location.reload()
          } catch (err: any) {
            alert('Restore failed: Incorrect password or corrupted backup file.')
          }
        }
        reader.readAsText(file)
      }
    }
    input.click()
  }

  return (
    <div className="max-w-7xl mx-auto pb-24 relative">
      <PageHeader
        title="Settings"
        subtitle="Manage your account preferences and platform configuration."
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
        
        {/* Profile Identity */}
        <div className="finora-card p-6 border border-outline-variant/30 md:col-span-2">
          <div className="flex justify-between items-center mb-6">
             <h3 className="text-xs font-bold tracking-wider text-[#1f1b18] uppercase">Profile Identity</h3>
             <button onClick={() => setIsProfileModalOpen(true)} className="text-xs font-semibold text-[#795548] hover:text-[#5d4037]">Edit Details</button>
          </div>
          
          <div className="flex items-center gap-8">
            <div className="relative">
              <div className="w-20 h-20 rounded-full bg-surface-variant flex items-center justify-center overflow-hidden border-2 border-white shadow-sm">
                {user?.avatar_url ? (
                  <img src={user.avatar_url} alt="Avatar" className="w-full h-full object-cover" />
                ) : (
                  <span className="text-2xl font-bold text-on-surface-variant">{user?.full_name?.charAt(0) || 'U'}</span>
                )}
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 flex-1">
               <div>
                  <p className="text-xs text-on-surface-variant mb-1">Full Name</p>
                  <p className="font-semibold text-[#1f1b18]">{user?.full_name || 'Loading...'}</p>
               </div>
               <div>
                  <p className="text-xs text-on-surface-variant mb-1">Email Address</p>
                  <p className="font-semibold text-[#1f1b18]">{user?.email || 'Loading...'}</p>
               </div>
               <div>
                  <p className="text-xs text-on-surface-variant mb-1">Phone Number</p>
                  <p className="font-semibold text-[#1f1b18]">{user?.phone || 'Not provided'}</p>
               </div>
            </div>
          </div>
        </div>

        {/* Security & Access */}
        <div className="finora-card p-6 border border-outline-variant/30 flex flex-col">
          <div className="flex items-center gap-2 mb-8">
            <span className="material-symbols-outlined text-[#795548] text-[20px]">security</span>
            <h3 className="text-xs font-bold tracking-wider text-[#1f1b18] uppercase">Security & Access</h3>
          </div>
          
          <div className="space-y-6">
            <div className="flex justify-between items-center pb-6 border-b border-outline-variant/30">
              <div>
                <p className="font-semibold text-[#1f1b18]">Account Password</p>
                <p className="text-xs text-on-surface-variant mt-1">Manage your access credentials</p>
              </div>
              <button onClick={() => setIsPasswordModalOpen(true)} className="px-4 py-1.5 border border-outline-variant rounded-md text-xs font-semibold text-[#1f1b18] hover:bg-surface-variant/30 transition-colors">
                Update
              </button>
            </div>

            <div className="flex justify-between items-center pb-6 border-b border-outline-variant/30 opacity-60">
              <div>
                <p className="font-semibold text-[#1f1b18]">Two-Factor Authentication (2FA)</p>
                <p className="text-xs text-on-surface-variant mt-1">Enhance your account security</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold px-2 py-0.5 bg-surface-variant text-on-surface-variant rounded uppercase">COMING SOON</span>
              </div>
            </div>

            <div className="opacity-60">
               <div className="flex items-center justify-between mb-4">
                 <p className="text-sm font-semibold text-[#1f1b18]">Recent Login History</p>
                 <span className="text-[10px] font-bold px-2 py-0.5 bg-surface-variant text-on-surface-variant rounded uppercase">COMING SOON</span>
               </div>
               <div className="space-y-3">
                 <div className="flex justify-between items-center bg-surface-variant/30 p-3 rounded-md">
                   <div className="flex items-center gap-3">
                     <span className="material-symbols-outlined text-on-surface-variant text-[18px]">laptop_mac</span>
                     <span className="text-xs text-[#1f1b18]">New York, US • Chrome on macOS</span>
                   </div>
                   <span className="text-xs text-on-surface-variant">Today, 09:42 AM</span>
                 </div>
               </div>
            </div>
          </div>
        </div>

        {/* Appearance & Workspace */}
        <div className="finora-card p-6 border border-outline-variant/30 flex flex-col">
          <div className="flex items-center gap-2 mb-8">
            <span className="material-symbols-outlined text-[#795548] text-[20px]">palette</span>
            <h3 className="text-xs font-bold tracking-wider text-[#1f1b18] uppercase">Appearance & Workspace</h3>
          </div>

          <div className="space-y-6">
            <div>
              <p className="text-sm font-semibold text-[#1f1b18] mb-3">Interface Theme</p>
              <div className="flex bg-[#f6ece4] rounded-lg p-1 w-full">
                {['Light', 'Dark', 'Auto'].map((t) => (
                  <button 
                    key={t}
                    onClick={() => setTheme(t as any)}
                    className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-md text-sm font-semibold transition-colors ${theme === t ? 'bg-white shadow-sm text-[#1f1b18]' : 'text-[#5d4037]'}`}
                  >
                    <span className="material-symbols-outlined text-[16px]">
                      {t === 'Light' ? 'light_mode' : t === 'Dark' ? 'dark_mode' : 'settings_brightness'}
                    </span>
                    {t}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex justify-between items-center pb-6 border-b border-outline-variant/30">
              <div>
                <p className="font-semibold text-[#1f1b18]">Compact Mode</p>
                <p className="text-xs text-on-surface-variant mt-1">Increase information density across tables</p>
              </div>
              <button 
                onClick={() => setCompactMode(!compactMode)}
                className={`w-11 h-6 rounded-full transition-colors relative ${compactMode ? 'bg-[#795548]' : 'bg-surface-variant'}`}
              >
                <div className={`w-4 h-4 bg-white rounded-full absolute top-1 transition-transform ${compactMode ? 'left-6' : 'left-1'}`}></div>
              </button>
            </div>

            <div className="grid grid-cols-2 gap-4">
               <div>
                 <p className="text-xs text-on-surface-variant mb-2">Base Currency</p>
                 <div className="relative">
                   <select 
                     value={currency} 
                     onChange={(e) => setCurrency(e.target.value)}
                     className="w-full bg-[#f6ece4] border-none rounded-md py-2 pl-3 pr-8 text-sm font-semibold text-[#1f1b18] appearance-none focus:ring-1 focus:ring-primary/30 outline-none"
                   >
                     <option value="INR">INR (₹)</option>
                     <option value="USD">USD ($)</option>
                     <option value="EUR">EUR (€)</option>
                     <option value="GBP">GBP (£)</option>
                   </select>
                   <span className="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none text-[18px]">expand_more</span>
                 </div>
               </div>
               <div className="opacity-60 relative">
                 <p className="text-xs text-on-surface-variant mb-2">Language</p>
                 <div className="relative">
                   <select disabled className="w-full bg-[#f6ece4] border-none rounded-md py-2 pl-3 pr-8 text-sm font-semibold text-[#1f1b18] appearance-none">
                     <option>English (US)</option>
                   </select>
                   <span className="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none text-[18px]">expand_more</span>
                 </div>
                 <div className="absolute top-0 right-0">
                    <span className="text-[8px] font-bold px-1.5 py-0.5 bg-surface-variant text-on-surface-variant rounded uppercase">COMING SOON</span>
                 </div>
               </div>
            </div>
          </div>
        </div>

        {/* Notification Channels */}
        <div className="finora-card p-6 border border-outline-variant/30 opacity-60">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xs font-bold tracking-wider text-[#1f1b18] uppercase">Notification Channels</h3>
            <span className="text-[10px] font-bold px-2 py-0.5 bg-surface-variant text-on-surface-variant rounded uppercase">COMING SOON</span>
          </div>
          
          <div className="space-y-4 pb-6 border-b border-outline-variant/30">
            <label className="flex items-center justify-between cursor-not-allowed group">
               <div className="flex items-center gap-3">
                  <span className="material-symbols-outlined text-on-surface-variant text-[20px]">mail</span>
                  <span className="text-sm text-[#1f1b18]">Email Digests</span>
               </div>
               <input type="checkbox" disabled defaultChecked className="w-4 h-4 text-[#795548] bg-white border-outline-variant rounded focus:ring-[#795548]" />
            </label>
            <label className="flex items-center justify-between cursor-not-allowed group">
               <div className="flex items-center gap-3">
                  <span className="material-symbols-outlined text-on-surface-variant text-[20px]">notifications_active</span>
                  <span className="text-sm text-[#1f1b18]">Real-time Push</span>
               </div>
               <input type="checkbox" disabled defaultChecked className="w-4 h-4 text-[#795548] bg-white border-outline-variant rounded focus:ring-[#795548]" />
            </label>
            <label className="flex items-center justify-between cursor-not-allowed group">
               <div className="flex items-center gap-3">
                  <span className="material-symbols-outlined text-on-surface-variant text-[20px]">sms</span>
                  <span className="text-sm text-[#1f1b18]">SMS Critical Alerts</span>
               </div>
               <input type="checkbox" disabled className="w-4 h-4 text-[#795548] bg-white border-outline-variant rounded focus:ring-[#795548]" />
            </label>
          </div>
          <p className="text-[10px] text-on-surface-variant italic mt-4">SMS alerts may incur carrier charges.</p>
        </div>

        {/* Expense & Income Categories */}
        <div className="finora-card p-6 border border-outline-variant/30 flex flex-col md:col-span-2 lg:col-span-1">
          <div className="flex justify-between items-center mb-6">
             <h3 className="text-xs font-bold tracking-wider text-[#1f1b18] uppercase">Expense & Income Categories</h3>
             <button onClick={() => setIsCategoryModalOpen(true)} className="text-xs font-semibold text-[#795548] hover:text-[#5d4037] flex items-center gap-1">
                <span className="material-symbols-outlined text-[14px]">add</span> New Category
             </button>
          </div>
          
          <div className="grid grid-cols-2 gap-3 max-h-[160px] overflow-y-auto pr-2">
            {categories.map((cat: any) => (
              <div key={cat.id} className="flex items-center gap-3 p-3 border border-outline-variant/50 rounded-md bg-white">
                 <div className="w-2 h-2 rounded-full" style={{ backgroundColor: cat.color || '#795548' }}></div>
                 <span className="text-xs font-medium text-[#1f1b18] truncate">{cat.name}</span>
                 <span className="text-[10px] text-on-surface-variant ml-auto capitalize">{cat.type}</span>
              </div>
            ))}
            {categories.length === 0 && (
              <p className="text-xs text-on-surface-variant col-span-2 py-4 text-center">No categories found.</p>
            )}
          </div>
        </div>

        {/* Data Management */}
        <div className="finora-card p-6 border border-outline-variant/30 flex flex-col justify-center">
          <h3 className="text-xs font-bold tracking-wider text-[#1f1b18] uppercase mb-6">Data Management</h3>
          <div className="grid grid-cols-4 gap-2">
            <button onClick={handleImportJSONClick} className="flex flex-col items-center justify-center gap-2 p-4 rounded-lg hover:bg-surface-variant/30 transition-colors group relative">
              <span className="material-symbols-outlined text-[#795548] text-[24px] group-hover:-translate-y-0.5 transition-transform">upload_file</span>
              <span className="text-[10px] font-bold text-[#1f1b18]">Import .enc</span>
            </button>
            <button onClick={handleExportJSON} className="flex flex-col items-center justify-center gap-2 p-4 rounded-lg hover:bg-surface-variant/30 transition-colors group">
              <span className="material-symbols-outlined text-[#795548] text-[24px] group-hover:-translate-y-0.5 transition-transform">download</span>
              <span className="text-[10px] font-bold text-[#1f1b18]">Export .enc</span>
            </button>
            <button onClick={() => setIsBackupModalOpen(true)} className="flex flex-col items-center justify-center gap-2 p-4 rounded-lg hover:bg-surface-variant/30 transition-colors group relative">
              <span className="material-symbols-outlined text-[#795548] text-[24px] group-hover:-translate-y-0.5 transition-transform">cloud_sync</span>
              <span className="text-[10px] font-bold text-[#1f1b18]">Cloud Backup</span>
            </button>
            <button onClick={handleReset} className="flex flex-col items-center justify-center gap-2 p-4 rounded-lg hover:bg-red-50 transition-colors group">
              <span className="material-symbols-outlined text-[#d32f2f] text-[24px] group-hover:-translate-y-0.5 transition-transform">restore</span>
              <span className="text-[10px] font-bold text-[#d32f2f]">Reset Account</span>
            </button>
          </div>
        </div>

        {/* Platform Status */}
        <div className="finora-card p-6 border border-outline-variant/30 flex flex-col justify-between">
          <h3 className="text-xs font-bold tracking-wider text-[#1f1b18] uppercase mb-4">Platform Status</h3>
          <div className="space-y-3 mb-6">
             <div className="flex justify-between items-center text-xs">
               <span className="text-on-surface-variant">Version</span>
               <span className="font-semibold text-[#1f1b18]">4.12.0-stable</span>
             </div>
             <div className="flex justify-between items-center text-xs">
               <span className="text-on-surface-variant">Last Update</span>
               <span className="font-semibold text-[#1f1b18]">{new Date().toLocaleDateString()}</span>
             </div>
             <div className="flex justify-between items-center text-xs">
               <span className="text-on-surface-variant">Server Status</span>
               <span className="font-semibold text-[#1f1b18] flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-teal-600"></div> Operational</span>
             </div>
          </div>
          <div className="space-y-1.5 flex flex-col items-start">
            <a href="#" className="text-[10px] text-[#795548] hover:underline">Terms of Stewardship</a>
            <a href="#" className="text-[10px] text-[#795548] hover:underline">Global Privacy Policy</a>
            <a href="#" className="text-[10px] text-[#795548] hover:underline">System Logs</a>
          </div>
        </div>

      </div>

      {/* Floating Footer Actions */}
      <div className="fixed bottom-0 left-0 lg:left-64 right-0 p-4 bg-[#faf8f5]/90 backdrop-blur border-t border-outline-variant/30 flex justify-end items-center gap-4 z-50">
         <span className="text-[10px] text-on-surface-variant mr-auto hidden md:inline ml-4">Wealth Stewardship © 2024 Institutional Grade Asset Management</span>
         <button className="text-sm font-semibold text-[#1f1b18] hover:text-[#5d4037] px-4 py-2 transition-colors">Discard Changes</button>
         <button onClick={handleSaveConfig} className="bg-[#5d4037] hover:bg-[#4e342e] text-white px-6 py-2.5 rounded-lg text-sm font-semibold transition-colors shadow-sm">
           {updateProfileMutation.isPending ? 'Saving...' : 'Save Configuration'}
         </button>
      </div>

      {/* Profile Modal */}
      <Dialog open={isProfileModalOpen} onOpenChange={setIsProfileModalOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Edit Profile Identity</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleUpdateProfile} className="space-y-4 pt-4">
            <div className="space-y-2">
              <Label htmlFor="full_name">Full Name</Label>
              <Input id="full_name" value={profileForm.full_name} onChange={e => setProfileForm({...profileForm, full_name: e.target.value})} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="phone">Phone Number</Label>
              <Input id="phone" value={profileForm.phone} onChange={e => setProfileForm({...profileForm, phone: e.target.value})} />
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <button type="button" onClick={() => setIsProfileModalOpen(false)} className="px-4 py-2 text-sm font-medium hover:bg-surface-variant rounded-md transition-colors">Cancel</button>
              <button type="submit" disabled={updateProfileMutation.isPending} className="px-4 py-2 bg-primary text-on-primary rounded-md text-sm font-medium hover:bg-primary/90 transition-colors">
                {updateProfileMutation.isPending ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Password Modal */}
      <Dialog open={isPasswordModalOpen} onOpenChange={setIsPasswordModalOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Change Account Password</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleChangePassword} className="space-y-4 pt-4">
            <div className="space-y-2">
              <Label htmlFor="current_password">Current Password</Label>
              <Input id="current_password" type="password" value={passwordForm.current_password} onChange={e => setPasswordForm({...passwordForm, current_password: e.target.value})} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="new_password">New Password</Label>
              <Input id="new_password" type="password" value={passwordForm.new_password} onChange={e => setPasswordForm({...passwordForm, new_password: e.target.value})} required />
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <button type="button" onClick={() => setIsPasswordModalOpen(false)} className="px-4 py-2 text-sm font-medium hover:bg-surface-variant rounded-md transition-colors">Cancel</button>
              <button type="submit" disabled={changePasswordMutation.isPending} className="px-4 py-2 bg-primary text-on-primary rounded-md text-sm font-medium hover:bg-primary/90 transition-colors">
                {changePasswordMutation.isPending ? 'Updating...' : 'Update Password'}
              </button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Category Modal */}
      <Dialog open={isCategoryModalOpen} onOpenChange={setIsCategoryModalOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Create New Category</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateCategory} className="space-y-4 pt-4">
            <div className="space-y-2">
              <Label htmlFor="cat_name">Category Name</Label>
              <Input id="cat_name" value={categoryForm.name} onChange={e => setCategoryForm({...categoryForm, name: e.target.value})} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="cat_type">Type</Label>
              <select 
                id="cat_type" 
                value={categoryForm.type} 
                onChange={e => setCategoryForm({...categoryForm, type: e.target.value})}
                className="w-full h-10 px-3 py-2 rounded-md border border-input bg-background text-sm ring-offset-background"
              >
                <option value="expense">Expense</option>
                <option value="income">Income</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="cat_color">Color Hex (e.g. #795548)</Label>
              <Input id="cat_color" value={categoryForm.color} onChange={e => setCategoryForm({...categoryForm, color: e.target.value})} />
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <button type="button" onClick={() => setIsCategoryModalOpen(false)} className="px-4 py-2 text-sm font-medium hover:bg-surface-variant rounded-md transition-colors">Cancel</button>
              <button type="submit" disabled={createCategoryMutation.isPending} className="px-4 py-2 bg-primary text-on-primary rounded-md text-sm font-medium hover:bg-primary/90 transition-colors">
                {createCategoryMutation.isPending ? 'Creating...' : 'Create Category'}
              </button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Cloud Backup Modal */}
      <GoogleOAuthProvider clientId={process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || 'YOUR_GOOGLE_CLIENT_ID'}>
        <BackupRestoreModal open={isBackupModalOpen} onOpenChange={setIsBackupModalOpen} />
      </GoogleOAuthProvider>
    </div>
  )
}
