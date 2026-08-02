'use client'

import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { useGoogleLogin } from '@react-oauth/google'
import { settingsApi } from '@/lib/api'
import { encryptData, decryptData } from '@/lib/crypto'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

interface BackupRestoreModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function BackupRestoreModal({ open, onOpenChange }: BackupRestoreModalProps) {
  const [mode, setMode] = useState<'idle' | 'backup_pass' | 'restore_list' | 'restore_pass' | 'working' | 'success' | 'error'>('idle')
  const [progressText, setProgressText] = useState('')
  const [errorText, setErrorText] = useState('')
  const [password, setPassword] = useState('')
  const [accessToken, setAccessToken] = useState('')
  const [backupFiles, setBackupFiles] = useState<any[]>([])
  const [selectedFileId, setSelectedFileId] = useState('')

  // Google Login Hook
  const login = useGoogleLogin({
    scope: 'https://www.googleapis.com/auth/drive.file',
    onSuccess: (tokenResponse) => {
      setAccessToken(tokenResponse.access_token)
      if (mode === 'idle') {
        // Decide what to do next based on what button was clicked
        // Wait, we need separate buttons for Backup and Restore before login.
      }
    },
    onError: () => {
      setErrorText('Google authentication failed.')
      setMode('error')
    }
  })

  // Start Backup Flow
  const startBackupFlow = () => {
    setMode('backup_pass')
    setPassword('')
  }

  // Start Restore Flow
  const startRestoreFlow = () => {
    setMode('working')
    setProgressText('Authenticating with Google...')
    login()
    // The onSuccess callback needs context of which flow we are in.
    // A better approach is to wrap login inside a promise or use flags.
  }

  // Helper for Google Drive API
  const getDriveFolder = async (token: string) => {
    const q = encodeURIComponent("name='Finora Backups' and mimeType='application/vnd.google-apps.folder' and trashed=false")
    const res = await fetch(`https://www.googleapis.com/drive/v3/files?q=${q}&fields=files(id, name)`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    const data = await res.json()
    if (data.files && data.files.length > 0) return data.files[0].id
    return null
  }

  const createDriveFolder = async (token: string) => {
    const res = await fetch('https://www.googleapis.com/drive/v3/files', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'Finora Backups', mimeType: 'application/vnd.google-apps.folder' })
    })
    const data = await res.json()
    return data.id
  }

  // Execute Backup
  const executeBackup = async (token: string) => {
    try {
      setMode('working')
      setProgressText('Exporting data from database...')
      const payload = await settingsApi.exportData()

      setProgressText('Encrypting backup securely...')
      const encryptedBlob = await encryptData(payload, password)

      setProgressText('Connecting to Google Drive...')
      let folderId = await getDriveFolder(token)
      if (!folderId) {
        folderId = await createDriveFolder(token)
      }

      setProgressText('Uploading to Google Drive...')
      const fileName = `backup-${new Date().toISOString().replace(/[:.]/g, '-')}.finora.enc`
      
      const metadata = {
        name: fileName,
        parents: [folderId]
      }
      
      const form = new FormData()
      form.append('metadata', new Blob([JSON.stringify(metadata)], { type: 'application/json' }))
      form.append('file', new Blob([encryptedBlob], { type: 'text/plain' }))

      const uploadRes = await fetch('https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: form
      })

      if (!uploadRes.ok) throw new Error('Failed to upload to Google Drive')
      
      setMode('success')
      setProgressText('Backup completed successfully!')
    } catch (e: any) {
      setErrorText(e.message || 'An error occurred during backup.')
      setMode('error')
    }
  }

  // Execute Restore
  const listRestoreFiles = async (token: string) => {
    try {
      let folderId = await getDriveFolder(token)
      if (!folderId) {
        throw new Error('No backups found in your Google Drive.')
      }

      const q = encodeURIComponent(`'${folderId}' in parents and trashed=false`)
      const res = await fetch(`https://www.googleapis.com/drive/v3/files?q=${q}&orderBy=createdTime desc&fields=files(id, name, createdTime)`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      const data = await res.json()
      
      if (!data.files || data.files.length === 0) {
        throw new Error('No backups found in your Google Drive.')
      }

      setBackupFiles(data.files)
      setMode('restore_list')
    } catch (e: any) {
      setErrorText(e.message || 'An error occurred fetching backups.')
      setMode('error')
    }
  }

  const executeRestore = async (token: string) => {
    try {
      setMode('working')
      setProgressText('Downloading backup from Google Drive...')
      
      const res = await fetch(`https://www.googleapis.com/drive/v3/files/${selectedFileId}?alt=media`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      const encryptedData = await res.text()

      setProgressText('Decrypting backup...')
      let decryptedPayload
      try {
        decryptedPayload = await decryptData(encryptedData, password)
      } catch (e) {
        throw new Error('Invalid password or corrupted backup.')
      }

      setProgressText('Restoring data to database (this may take a moment)...')
      await settingsApi.restoreData(decryptedPayload)

      setMode('success')
      setProgressText('Restore completed successfully! Reloading...')
      setTimeout(() => window.location.reload(), 2000)
    } catch (e: any) {
      setErrorText(e.message || 'An error occurred during restore.')
      setMode('error')
    }
  }

  // Wrapper for login to inject action
  const handleAuth = (action: 'backup' | 'restore') => {
    const lg = useGoogleLogin({
      scope: 'https://www.googleapis.com/auth/drive.file',
      onSuccess: (tokenResponse) => {
        setAccessToken(tokenResponse.access_token)
        if (action === 'backup') executeBackup(tokenResponse.access_token)
        if (action === 'restore') listRestoreFiles(tokenResponse.access_token)
      },
      onError: () => {
        setErrorText('Google authentication failed.')
        setMode('error')
      }
    })
    lg()
  }

  // To solve the hooks rule inside a handler, we should just use a single login wrapper
  const [intendedAction, setIntendedAction] = useState<'backup' | 'restore' | null>(null)
  
  const googleLogin = useGoogleLogin({
    scope: 'https://www.googleapis.com/auth/drive.file',
    onSuccess: (tokenResponse) => {
      setAccessToken(tokenResponse.access_token)
      if (intendedAction === 'backup') executeBackup(tokenResponse.access_token)
      if (intendedAction === 'restore') listRestoreFiles(tokenResponse.access_token)
    },
    onError: () => {
      setErrorText('Google authentication failed.')
      setMode('error')
    }
  })

  const initiateBackup = () => {
    if (!password) return
    setIntendedAction('backup')
    setMode('working')
    setProgressText('Authenticating with Google...')
    googleLogin()
  }

  const initiateRestoreSearch = () => {
    setIntendedAction('restore')
    setMode('working')
    setProgressText('Authenticating with Google...')
    googleLogin()
  }

  return (
    <Dialog open={open} onOpenChange={(val) => {
      if (mode === 'working') return // Prevent closing while working
      onOpenChange(val)
      if (!val) {
        setTimeout(() => setMode('idle'), 300)
      }
    }}>
      <DialogContent className="sm:max-w-[450px]">
        <DialogHeader>
          <DialogTitle>Cloud Backup & Restore</DialogTitle>
        </DialogHeader>
        
        <div className="py-4">
          
          {mode === 'idle' && (
            <div className="flex flex-col gap-4">
              <p className="text-sm text-on-surface-variant mb-2">
                Securely back up your entire financial history to your personal Google Drive. 
                All data is encrypted before leaving your device using AES-256.
              </p>
              <button onClick={() => setMode('backup_pass')} className="w-full py-3 bg-[#4caf50] hover:bg-[#43a047] text-white font-semibold rounded-md transition-colors flex items-center justify-center gap-2">
                <span className="material-symbols-outlined">cloud_upload</span> Back Up to Google Drive
              </button>
              <button onClick={initiateRestoreSearch} className="w-full py-3 border border-outline-variant hover:bg-surface-variant/30 text-[#1f1b18] font-semibold rounded-md transition-colors flex items-center justify-center gap-2">
                <span className="material-symbols-outlined text-[#795548]">cloud_download</span> Restore from Google Drive
              </button>
            </div>
          )}

          {mode === 'backup_pass' && (
            <div className="space-y-4">
              <p className="text-sm font-medium text-[#1f1b18]">Set an Encryption Password</p>
              <p className="text-xs text-on-surface-variant">
                Your data will be encrypted before uploading. You will need this exact password to restore your backup later. If you lose this password, your backup cannot be recovered.
              </p>
              <div className="space-y-2 pt-2">
                <Label>Backup Password</Label>
                <Input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Strong password" />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button onClick={() => setMode('idle')} className="px-4 py-2 text-sm font-medium hover:bg-surface-variant rounded-md">Cancel</button>
                <button onClick={initiateBackup} disabled={!password || password.length < 4} className="px-4 py-2 bg-[#4caf50] text-white rounded-md text-sm font-medium disabled:opacity-50">Continue</button>
              </div>
            </div>
          )}

          {mode === 'restore_list' && (
            <div className="space-y-4">
              <p className="text-sm font-medium text-[#1f1b18]">Select a Backup</p>
              <div className="max-h-[200px] overflow-y-auto space-y-2 border border-outline-variant/30 rounded-md p-2">
                {backupFiles.map(f => (
                  <button 
                    key={f.id}
                    onClick={() => setSelectedFileId(f.id)}
                    className={`w-full text-left p-3 rounded-md text-sm transition-colors ${selectedFileId === f.id ? 'bg-[#e8f5e9] border-[#4caf50]' : 'hover:bg-surface-variant/30'} border border-transparent`}
                  >
                    <div className="font-semibold">{new Date(f.createdTime).toLocaleString()}</div>
                    <div className="text-xs text-on-surface-variant truncate">{f.name}</div>
                  </button>
                ))}
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button onClick={() => setMode('idle')} className="px-4 py-2 text-sm font-medium hover:bg-surface-variant rounded-md">Cancel</button>
                <button 
                  onClick={() => { setMode('restore_pass'); setPassword(''); }} 
                  disabled={!selectedFileId} 
                  className="px-4 py-2 bg-[#4caf50] text-white rounded-md text-sm font-medium disabled:opacity-50"
                >Next</button>
              </div>
            </div>
          )}

          {mode === 'restore_pass' && (
            <div className="space-y-4">
              <p className="text-sm font-medium text-[#1f1b18]">Enter Encryption Password</p>
              <p className="text-xs text-on-surface-variant">
                Please enter the password you used when creating this backup.
              </p>
              <div className="space-y-2 pt-2">
                <Label>Backup Password</Label>
                <Input type="password" value={password} onChange={e => setPassword(e.target.value)} />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button onClick={() => setMode('restore_list')} className="px-4 py-2 text-sm font-medium hover:bg-surface-variant rounded-md">Back</button>
                <button onClick={() => executeRestore(accessToken)} disabled={!password} className="px-4 py-2 bg-[#4caf50] text-white rounded-md text-sm font-medium disabled:opacity-50">Restore Data</button>
              </div>
            </div>
          )}

          {mode === 'working' && (
            <div className="flex flex-col items-center justify-center py-8 text-center space-y-4">
              <div className="w-12 h-12 border-4 border-surface-variant border-t-[#4caf50] rounded-full animate-spin"></div>
              <p className="font-medium text-[#1f1b18]">{progressText}</p>
            </div>
          )}

          {mode === 'success' && (
            <div className="flex flex-col items-center justify-center py-8 text-center space-y-4">
              <div className="w-16 h-16 bg-[#e8f5e9] rounded-full flex items-center justify-center text-[#4caf50]">
                <span className="material-symbols-outlined text-[32px]">check_circle</span>
              </div>
              <p className="font-bold text-[#1f1b18]">{progressText}</p>
              <button onClick={() => onOpenChange(false)} className="px-6 py-2 bg-[#4caf50] text-white rounded-md text-sm font-medium">Done</button>
            </div>
          )}

          {mode === 'error' && (
            <div className="flex flex-col items-center justify-center py-8 text-center space-y-4">
              <div className="w-16 h-16 bg-[#ffebee] rounded-full flex items-center justify-center text-[#f44336]">
                <span className="material-symbols-outlined text-[32px]">error</span>
              </div>
              <p className="font-bold text-[#f44336]">Operation Failed</p>
              <p className="text-sm text-[#1f1b18] px-4">{errorText}</p>
              <button onClick={() => setMode('idle')} className="px-6 py-2 border border-outline-variant hover:bg-surface-variant/30 rounded-md text-sm font-medium">Try Again</button>
            </div>
          )}

        </div>
      </DialogContent>
    </Dialog>
  )
}
