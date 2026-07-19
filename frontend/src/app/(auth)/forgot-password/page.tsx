'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useForm as useRHForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { authApi } from '@/lib/api/auth'
import { toast } from 'sonner'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'

const schema = z.object({
  email: z.string().email('Invalid email address'),
})

type FormValues = z.infer<typeof schema>

export default function ForgotPasswordPage() {
  const [loading, setLoading] = useState(false)
  const [resetToken, setResetToken] = useState<string | null>(null)

  const { register, handleSubmit, formState: { errors } } = useRHForm<FormValues>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data: FormValues) => {
    try {
      setLoading(true)
      const res = await authApi.forgotPassword(data.email)
      if (res.data.success && res.data.data) {
        setResetToken(res.data.data.reset_token)
        toast.success('Reset token generated')
      }
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to request reset')
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
          <h2 className="text-2xl font-display font-bold text-on-surface mb-2">Forgot Password</h2>
          <p className="text-on-surface-variant text-sm">Enter your email to receive a reset token.</p>
        </div>

        {!resetToken ? (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-on-surface mb-1">Email</label>
              <input
                {...register('email')}
                type="email"
                placeholder="Enter your email"
                className="w-full px-4 py-2 rounded-lg border border-outline-variant bg-surface-container-lowest focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors"
              />
              {errors.email && <p className="mt-1 text-sm text-error">{errors.email.message}</p>}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary justify-center py-2"
            >
              {loading ? <LoadingSpinner size="sm" color="white" /> : 'Get Reset Token'}
            </button>
          </form>
        ) : (
          <div className="space-y-6">
            <div className="bg-surface-variant p-4 rounded-lg border border-outline-variant text-center">
              <p className="text-sm text-on-surface-variant mb-2">Copy this token and use it on the reset password page:</p>
              <code className="block bg-surface-container-lowest p-2 rounded text-primary font-mono text-sm break-all select-all">
                {resetToken}
              </code>
            </div>
            <Link href="/reset-password" className="w-full btn-primary justify-center py-2 text-center block">
              Go to Reset Password
            </Link>
          </div>
        )}

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
