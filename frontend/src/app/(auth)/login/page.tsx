'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useForm as useRHForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { authApi } from '@/lib/api/auth'
import { useAuthStore } from '@/store/authStore'
import { toast } from 'sonner'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
})

type LoginForm = z.infer<typeof loginSchema>

export default function LoginPage() {
  const router = useRouter()
  const { setAuth } = useAuthStore()
  const [loading, setLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useRHForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data: LoginForm) => {
    try {
      setLoading(true)
      const res = await authApi.login(data)
      if (res.data.success && res.data.data) {
        const { user, tokens } = res.data.data
        setAuth(user, tokens.access_token, tokens.refresh_token)
        toast.success('Welcome back!')
        router.push('/')
      }
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen">
      {/* Left Panel */}
      <div className="hidden lg:flex flex-1 flex-col justify-center px-20 text-white bg-gradient-to-br from-primary to-primary-container">
        <div className="mb-12">
          <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center mb-6 backdrop-blur-sm">
            <span className="font-display text-4xl font-bold">F</span>
          </div>
          <h1 className="text-5xl font-display font-bold mb-4">Finora</h1>
          <p className="text-xl text-primary-fixed-dim">Where your financial future begins.</p>
        </div>
        <ul className="space-y-6">
          <li className="flex items-center gap-4 text-lg">
            <span className="material-symbols-outlined filled">check_circle</span>
            Track income and expenses effortlessly
          </li>
          <li className="flex items-center gap-4 text-lg">
            <span className="material-symbols-outlined filled">check_circle</span>
            Monitor investments and wealth growth
          </li>
          <li className="flex items-center gap-4 text-lg">
            <span className="material-symbols-outlined filled">check_circle</span>
            Achieve your financial goals faster
          </li>
        </ul>
      </div>

      {/* Right Panel */}
      <div className="flex-1 flex flex-col justify-center px-8 sm:px-20 bg-background">
        <div className="w-full max-w-md mx-auto">
          <div className="mb-10 lg:hidden">
            <div className="w-12 h-12 bg-primary rounded-xl flex items-center justify-center mb-4">
              <span className="font-display text-2xl font-bold text-white">F</span>
            </div>
            <h1 className="text-3xl font-display font-bold text-on-surface">Finora</h1>
          </div>

          <h2 className="text-3xl font-display font-bold text-on-surface mb-2">Welcome back</h2>
          <p className="text-on-surface-variant mb-8">Enter your details to access your account.</p>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
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

            <div>
              <label className="block text-sm font-medium text-on-surface mb-1">Password</label>
              <input
                {...register('password')}
                type="password"
                placeholder="Enter your password"
                className="w-full px-4 py-2 rounded-lg border border-outline-variant bg-surface-container-lowest focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors"
              />
              {errors.password && <p className="mt-1 text-sm text-error">{errors.password.message}</p>}
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" className="w-4 h-4 rounded border-outline-variant text-primary focus:ring-primary" />
                <span className="text-sm text-on-surface-variant">Remember me</span>
              </label>
              <Link href="/forgot-password" className="text-sm font-medium text-primary hover:text-primary-container">
                Forgot password?
              </Link>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary justify-center py-3 text-base mt-2"
            >
              {loading ? <LoadingSpinner size="sm" color="white" /> : 'Log in'}
            </button>
          </form>

          <p className="mt-8 text-center text-sm text-on-surface-variant">
            Don't have an account?{' '}
            <Link href="/register" className="font-medium text-primary hover:text-primary-container">
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
