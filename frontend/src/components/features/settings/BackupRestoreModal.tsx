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

// ── Google Drive helpers ───────────────────────────────────────────────────────
const DRIVE_FILES_URL = 'https://www.googleapis.com/drive/v3/files'
const DRIVE_UPLOAD_URL = 'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart'

async function driveGet(url: string, token: string) {
  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } })
  if (!res.ok) {
    let msg = `Drive API error (${res.status})`
    try { const j = await res.json(); msg = j?.error?.message || msg } catch {}
    throw new Error(msg)
  }
  return res.json()
}

async function getDriveFolder(token: string): Promise<string | null> {
  const q = encodeURIComponent("name='Finora Backups' and mimeType='application/vnd.google-apps.folder' and trashed=false")
  const data = await driveGet(`${DRIVE_FILES_URL}?q=${q}&spaces=drive&fields=files(id,name)`, token)
  return data.files?.length > 0 ? data.files[0].id : null
}

async function createDriveFolder(token: string): Promise<string> {
  const res = await fetch(DRIVE_FILES_URL, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: 'Finora Backups', mimeType: 'application/vnd.google-apps.folder' }),
  })
  if (!res.ok) {
    let msg = `Failed to create folder (${res.status})`
    try { const j = await res.json(); msg = j?.error?.message || msg } catch {}
    throw new Error(msg)
  }
  const data = await res.json()
  return data.id
}

async function listDriveBackups(folderId: string, token: string) {
  const q = encodeURIComponent(`'${folderId}' in parents and trashed=false`)
  const data = await driveGet(`${DRIVE_FILES_URL}?q=${q}&spaces=drive&orderBy=createdTime desc&fields=files(id,name,createdTime)`, token)
  return data.files || []
}

async function uploadToDrive(token: string, folderId: string, content: string, fileName: string) {
  const metadata = { name: fileName, parents: [folderId] }
  const form = new FormData()
  form.append('metadata', new Blob([JSON.stringify(metadata)], { type: 'application/json' }))
  form.append('file', new Blob([content], { type: 'text/plain' }))
  const res = await fetch(DRIVE_UPLOAD_URL, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  })
  if (!res.ok) {
    let msg = `Upload failed (${res.status})`
    try { const j = await res.json(); msg = j?.error?.message || msg } catch {}
    throw new Error(msg)
  }
}

async function downloadFromDrive(fileId: string, token: string): Promise<string> {
  const res = await fetch(`${DRIVE_FILES_URL}/${fileId}?alt=media`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) {
    let msg = `Download failed (${res.status})`
    try { const j = await res.json(); msg = j?.error?.message || msg } catch {}
    throw new Error(msg)
  }
  return res.text()
}

// ── Component ──────────────────────────────────────────────────────────────────
export function BackupRestoreModal({ open, onOpenChange }: BackupRestoreModalProps) {
  const [mode, setMode]                     = useState<'idle' | 'backup_pass' | 'restore_list' | 'restore_pass' | 'working' | 'success' | 'error'>('idle')
  const [progressText, setProgressText]     = useState('')
  const [errorText, setErrorText]           = useState('')
  const [password, setPassword]             = useState('')
  const [backupFiles, setBackupFiles]       = useState<any[]>([])
  const [selectedFileId, setSelectedFileId] = useState('')
  const [driveToken, setDriveToken]         = useState('')

  const setError = (msg: string) => { setErrorText(msg); setMode('error') }
  const setWorking = (msg: string) => { setProgressText(msg); setMode('working') }

  // ── Backup execution ──────────────────────────────────────────────────────────
  const runBackup = async (token: string, pass: string) => {
    try {
      setWorking('Exporting your Finora data...')
      const payload = await settingsApi.exportData()

      setProgressText('Encrypting with AES-256-GCM...')
      const encrypted = await encryptData(payload, pass)

      setProgressText('Connecting to Google Drive...')
      let folderId = await getDriveFolder(token)
      if (!folderId) {
        setProgressText('Creating Finora Backups folder...')
        folderId = await createDriveFolder(token)
      }

      setProgressText('Uploading encrypted backup...')
      const fileName = `finora-backup-${new Date().toISOString().replace(/[:.]/g, '-')}.enc`
      await uploadToDrive(token, folderId, encrypted, fileName)

      setProgressText('Backup completed successfully!')
      setMode('success')
    } catch (e: any) {
      setError(e.message || 'An unexpected error occurred during backup.')
    }
  }

  // ── Restore: list backups ─────────────────────────────────────────────────────
  const runListBackups = async (token: string) => {
    try {
      setProgressText('Searching for backups in Google Drive...')
      const folderId = await getDriveFolder(token)
      if (!folderId) throw new Error('No "Finora Backups" folder found. Make a backup first.')
      const files = await listDriveBackups(folderId, token)
      if (!files.length) throw new Error('No backup files found in your Google Drive.')
      setBackupFiles(files)
      setMode('restore_list')
    } catch (e: any) {
      setError(e.message || 'An error occurred fetching backups.')
    }
  }

  // ── Restore execution ─────────────────────────────────────────────────────────
  const runRestore = async (token: string, pass: string, fileId: string) => {
    try {
      setWorking('Downloading backup from Google Drive...')
      const encryptedData = await downloadFromDrive(fileId, token)

      setProgressText('Decrypting backup...')
      let decryptedPayload: any
      try {
        decryptedPayload = await decryptData(encryptedData, pass)
      } catch {
        throw new Error('Incorrect password or corrupted backup file.')
      }

      setProgressText('Restoring your data (this may take a moment)...')
      await settingsApi.restoreData(decryptedPayload)

      setProgressText('Restore complete! Reloading in 2 seconds...')
      setMode('success')
      setTimeout(() => window.location.reload(), 2000)
    } catch (e: any) {
      setError(e.message || 'An error occurred during restore.')
    }
  }

  // ── Google OAuth hooks — ONE hook per action (React rules require top-level only) ──
  // Scope: drive — gives full Drive access needed for file listing + folder creation.
  // drive.file scope is too restrictive: it only shows files this app created,
  // so querying for the folder on first run succeeds (200) but folder listing
  // from another device/session returns empty even though the folder exists.
  const googleLoginForBackup = useGoogleLogin({
    scope: 'https://www.googleapis.com/auth/drive',
    onSuccess: (resp) => {
      const token = resp.access_token
      setDriveToken(token)
      // password is captured from state at this point (OAuth popup takes seconds)
      runBackup(token, password)
    },
    onError: (err) => setError(`Google sign-in failed. ${err.error_description || ''}`),
  })

  const googleLoginForRestore = useGoogleLogin({
    scope: 'https://www.googleapis.com/auth/drive',
    onSuccess: (resp) => {
      const token = resp.access_token
      setDriveToken(token)
      runListBackups(token)
    },
    onError: (err) => setError(`Google sign-in failed. ${err.error_description || ''}`),
  })

  // ── Handlers ──────────────────────────────────────────────────────────────────
  const initiateBackup = () => {
    if (!password || password.length < 4) return
    setWorking('Authenticating with Google...')
    googleLoginForBackup()
  }

  const initiateRestoreSearch = () => {
    setWorking('Authenticating with Google...')
    googleLoginForRestore()
  }

  // For restore pass → execute: use already-stored driveToken
  const initiateRestore = () => {
    if (!driveToken) {
      // Token expired or not set — re-auth
      setWorking('Re-authenticating with Google...')
      // We can't call the restore hook here (it's already defined), but we can
      // re-trigger restore search which will re-auth and re-list. User re-selects file.
      googleLoginForRestore()
      return
    }
    runRestore(driveToken, password, selectedFileId)
  }

  const handleClose = (val: boolean) => {
    if (mode === 'working') return
    onOpenChange(val)
    if (!val) {
      setTimeout(() => {
        setMode('idle')
        setPassword('')
        setSelectedFileId('')
        setDriveToken('')
        setBackupFiles([])
        setErrorText('')
      }, 300)
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[480px]">
        <DialogHeader>
          <DialogTitle>Cloud Backup &amp; Restore</DialogTitle>
        </DialogHeader>

        <div className="py-2 space-y-2">

          {/* ── Idle ── */}
          {mode === 'idle' && (
            <div className="flex flex-col gap-4">
              <p className="text-sm text-on-surface-variant">
                Back up your entire Finora history to your personal Google Drive.
                Data is encrypted with <strong>AES-256-GCM</strong> before leaving your device.
              </p>
              <div className="bg-primary/5 border border-primary/20 rounded-lg p-3 text-xs text-on-surface-variant space-y-1">
                <p className="font-semibold text-primary">What you need:</p>
                <p>• A Google account with Google Drive enabled</p>
                <p>• Google Drive API enabled in Google Cloud Console</p>
                <p>• <code>https://www.googleapis.com/auth/drive</code> scope in OAuth consent screen</p>
              </div>
              <button
                onClick={() => setMode('backup_pass')}
                className="w-full py-3 bg-primary hover:bg-primary/90 text-white font-semibold rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                <span className="material-symbols-outlined">cloud_upload</span>
                Back Up to Google Drive
              </button>
              <button
                onClick={initiateRestoreSearch}
                className="w-full py-3 border border-outline-variant hover:bg-surface-variant/30 text-[#1f1b18] font-semibold rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                <span className="material-symbols-outlined text-primary">cloud_download</span>
                Restore from Google Drive
              </button>
            </div>
          )}

          {/* ── Set backup password ── */}
          {mode === 'backup_pass' && (
            <div className="space-y-4">
              <div>
                <p className="text-sm font-semibold text-[#1f1b18]">Set an Encryption Password</p>
                <p className="text-xs text-on-surface-variant mt-1">
                  All data is encrypted before uploading. You must use this exact password to restore.{' '}
                  <strong>There is no way to recover a forgotten password.</strong>
                </p>
              </div>
              <div className="space-y-1.5">
                <Label>Backup Password (min 4 characters)</Label>
                <Input
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="Choose a strong password…"
                  autoFocus
                  onKeyDown={e => e.key === 'Enter' && initiateBackup()}
                />
              </div>
              <div className="flex justify-end gap-2 pt-1">
                <button onClick={() => setMode('idle')} className="px-4 py-2 text-sm font-medium hover:bg-surface-variant rounded-md">Cancel</button>
                <button
                  onClick={initiateBackup}
                  disabled={!password || password.length < 4}
                  className="px-4 py-2 bg-primary text-white rounded-lg text-sm font-semibold disabled:opacity-50 hover:bg-primary/90 transition-colors"
                >
                  Sign in with Google &amp; Back Up
                </button>
              </div>
            </div>
          )}

          {/* ── Restore: select backup file ── */}
          {mode === 'restore_list' && (
            <div className="space-y-4">
              <p className="text-sm font-semibold text-[#1f1b18]">Select a Backup to Restore</p>
              <div className="max-h-[220px] overflow-y-auto space-y-2 border border-outline-variant/30 rounded-lg p-2">
                {backupFiles.map(f => (
                  <button
                    key={f.id}
                    onClick={() => setSelectedFileId(f.id)}
                    className={`w-full text-left p-3 rounded-lg text-sm transition-colors border
                      ${selectedFileId === f.id
                        ? 'bg-primary/10 border-primary/30'
                        : 'border-transparent hover:bg-surface-variant/30'}`}
                  >
                    <div className={`font-semibold ${selectedFileId === f.id ? 'text-primary' : 'text-[#1f1b18]'}`}>
                      {new Date(f.createdTime).toLocaleString()}
                    </div>
                    <div className="text-xs text-on-surface-variant truncate mt-0.5">{f.name}</div>
                  </button>
                ))}
              </div>
              <div className="flex justify-end gap-2">
                <button onClick={() => setMode('idle')} className="px-4 py-2 text-sm font-medium hover:bg-surface-variant rounded-md">Cancel</button>
                <button
                  onClick={() => { setMode('restore_pass'); setPassword('') }}
                  disabled={!selectedFileId}
                  className="px-4 py-2 bg-primary text-white rounded-lg text-sm font-semibold disabled:opacity-50 hover:bg-primary/90 transition-colors"
                >
                  Next
                </button>
              </div>
            </div>
          )}

          {/* ── Restore: enter password ── */}
          {mode === 'restore_pass' && (
            <div className="space-y-4">
              <div>
                <p className="text-sm font-semibold text-[#1f1b18]">Enter Encryption Password</p>
                <p className="text-xs text-on-surface-variant mt-1">Enter the password you set when this backup was created.</p>
              </div>
              <div className="space-y-1.5">
                <Label>Backup Password</Label>
                <Input
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="Your backup password…"
                  autoFocus
                  onKeyDown={e => e.key === 'Enter' && initiateRestore()}
                />
              </div>
              <div className="flex justify-end gap-2 pt-1">
                <button onClick={() => setMode('restore_list')} className="px-4 py-2 text-sm font-medium hover:bg-surface-variant rounded-md">Back</button>
                <button
                  onClick={initiateRestore}
                  disabled={!password}
                  className="px-4 py-2 bg-primary text-white rounded-lg text-sm font-semibold disabled:opacity-50 hover:bg-primary/90 transition-colors"
                >
                  Restore Data
                </button>
              </div>
            </div>
          )}

          {/* ── Working ── */}
          {mode === 'working' && (
            <div className="flex flex-col items-center justify-center py-12 text-center space-y-5">
              <div className="w-14 h-14 border-4 border-surface-variant border-t-primary rounded-full animate-spin" />
              <p className="font-semibold text-[#1f1b18] max-w-xs">{progressText}</p>
            </div>
          )}

          {/* ── Success ── */}
          {mode === 'success' && (
            <div className="flex flex-col items-center justify-center py-12 text-center space-y-4">
              <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
                <span className="material-symbols-outlined text-primary text-[36px]">check_circle</span>
              </div>
              <p className="font-bold text-[#1f1b18] text-lg">{progressText}</p>
              <button onClick={() => onOpenChange(false)} className="px-8 py-2 bg-primary text-white rounded-lg font-semibold hover:bg-primary/90 transition-colors">Done</button>
            </div>
          )}

          {/* ── Error ── */}
          {mode === 'error' && (
            <div className="flex flex-col items-center justify-center py-10 text-center space-y-4">
              <div className="w-16 h-16 bg-error/10 rounded-full flex items-center justify-center">
                <span className="material-symbols-outlined text-error text-[36px]">error</span>
              </div>
              <p className="font-bold text-error text-lg">Operation Failed</p>
              <p className="text-sm text-[#1f1b18] px-4 bg-surface-variant/40 rounded-lg py-3 max-w-sm break-words">{errorText}</p>
              {(errorText.includes('403') || errorText.includes('scope') || errorText.includes('Drive API')) && (
                <div className="text-xs text-on-surface-variant bg-primary/5 border border-primary/20 rounded-lg p-3 text-left max-w-sm space-y-1">
                  <p className="font-semibold text-primary">Setup checklist:</p>
                  <p>1. Enable <strong>Google Drive API</strong> in Google Cloud Console</p>
                  <p>2. Add <code>https://www.googleapis.com/auth/drive</code> to OAuth consent screen scopes</p>
                  <p>3. Add your email to test users (if app is in testing mode)</p>
                </div>
              )}
              <button onClick={() => setMode('idle')} className="px-6 py-2 border border-outline-variant hover:bg-surface-variant/30 rounded-lg text-sm font-semibold transition-colors">Try Again</button>
            </div>
          )}

        </div>
      </DialogContent>
    </Dialog>
  )
}
