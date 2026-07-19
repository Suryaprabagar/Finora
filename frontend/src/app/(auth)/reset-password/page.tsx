'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useForm as useRHForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { authApi } from '@/lib/api/auth'
import { toast } from 'sonner'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'

const schema = z.object({
  token: z.string().min(1, 'Token is required'),
  newPassword: z.string().min(8, 'Password must be at least 8 characters'),
  confirmPassword: z.string()
}).refine((data) => data.newPassword === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
})

type FormValues = z.infer<typeof schema>

export default function ResetPasswordPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)

  const { register, handleSubmit, formState: { errors } } = useRHForm<FormValues>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data: FormValues) => {
    try {
      setLoading(true)
      const res = await authApi.resetPassword(data.token, data.newPassword)
      if (res.data.success) {
        toast.success('Password reset successfully')
        router.push('/login')
      }
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to reset password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-md finora-card p-8">
        <div className="text-center mb-8">
          <div className="w-12 h-12 bg-primary rounded-xl flex items-center justify-center mx-auto mb-4">
            <span className="font-display text-2xl font-bold text-white">F</span>
          </div>
          <h2 className="text-2xl font-display font-bold text-on-surface mb-2">Reset Password</h2>
          <p className="text-on-surface-variant text-sm">Enter your reset token and new password.</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-on-surface mb-1">Reset Token</label>
            <input
              {...register('token')}
              type="text"
              placeholder="Paste token here"
              className="w-full px-4 py-2 rounded-lg border border-outline-variant bg-surface-container-lowest focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors font-mono text-sm"
            />
            {errors.token && <p className="mt-1 text-sm text-error">{errors.token.message}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-on-surface mb-1">New Password</label>
            <input
              {...register('newPassword')}
              type="password"
              placeholder="At least 8 characters"
              className="w-full px-4 py-2 rounded-lg border border-outline-variant bg-surface-container-lowest focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors"
            />
            {errors.newPassword && <p className="mt-1 text-sm text-error">{errors.newPassword.message}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-on-surface mb-1">Confirm Password</label>
            <input
              {...register('confirmPassword')}
              type="password"
              placeholder="Repeat password"
              className="w-full px-4 py-2 rounded-lg border border-outline-variant bg-surface-container-lowest focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors"
            />
            {errors.confirmPassword && <p className="mt-1 text-sm text-error">{errors.confirmPassword.message}</p>}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full btn-primary justify-center py-2 mt-2"
          >
            {loading ? <LoadingSpinner size="sm" color="white" /> : 'Reset Password'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <Link href="/login" className="text-sm font-medium text-primary hover:text-primary-container flex items-center justify-center gap-2">
            <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>arrow_back</span>
            Back to login
          </Link>
        </div>
      </div>
    </div>
  )
}
