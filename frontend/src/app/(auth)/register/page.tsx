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

const registerSchema = z.object({
  full_name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirmPassword: z.string()
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
})

type RegisterForm = z.infer<typeof registerSchema>

export default function RegisterPage() {
  const router = useRouter()
  const { setAuth } = useAuthStore()
  const [loading, setLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useRHForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
  })

  const onSubmit = async (data: RegisterForm) => {
    try {
      setLoading(true)
      const res = await authApi.register({
        full_name: data.full_name,
        email: data.email,
        password: data.password
      })
      if (res.data.success && res.data.data) {
        const { user, tokens } = res.data.data
        setAuth(user, tokens.access_token, tokens.refresh_token)
        toast.success('Account created successfully!')
        router.push('/')
      }
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Registration failed')
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
          <p className="text-xl text-primary-fixed-dim">Take control of your finances today.</p>
        </div>
        <ul className="space-y-6">
          <li className="flex items-center gap-4 text-lg">
            <span className="material-symbols-outlined filled">check_circle</span>
            Simple and intuitive dashboard
          </li>
          <li className="flex items-center gap-4 text-lg">
            <span className="material-symbols-outlined filled">check_circle</span>
            Detailed financial reports
          </li>
          <li className="flex items-center gap-4 text-lg">
            <span className="material-symbols-outlined filled">check_circle</span>
            Secure and private data
          </li>
        </ul>
      </div>

      {/* Right Panel */}
      <div className="flex-1 flex flex-col justify-center px-8 sm:px-20 bg-background py-10">
        <div className="w-full max-w-md mx-auto">
          <div className="mb-10 lg:hidden">
            <div className="w-12 h-12 bg-primary rounded-xl flex items-center justify-center mb-4">
              <span className="font-display text-2xl font-bold text-white">F</span>
            </div>
            <h1 className="text-3xl font-display font-bold text-on-surface">Finora</h1>
          </div>

          <h2 className="text-3xl font-display font-bold text-on-surface mb-2">Create an account</h2>
          <p className="text-on-surface-variant mb-8">Join Finora to start managing your wealth.</p>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-on-surface mb-1">Full Name</label>
              <input
                {...register('full_name')}
                type="text"
                placeholder="John Doe"
                className="w-full px-4 py-2 rounded-lg border border-outline-variant bg-surface-container-lowest focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors"
              />
              {errors.full_name && <p className="mt-1 text-sm text-error">{errors.full_name.message}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-on-surface mb-1">Email</label>
              <input
                {...register('email')}
                type="email"
                placeholder="john@example.com"
                className="w-full px-4 py-2 rounded-lg border border-outline-variant bg-surface-container-lowest focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors"
              />
              {errors.email && <p className="mt-1 text-sm text-error">{errors.email.message}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-on-surface mb-1">Password</label>
              <input
                {...register('password')}
                type="password"
                placeholder="At least 8 characters"
                className="w-full px-4 py-2 rounded-lg border border-outline-variant bg-surface-container-lowest focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors"
              />
              {errors.password && <p className="mt-1 text-sm text-error">{errors.password.message}</p>}
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
              className="w-full btn-primary justify-center py-3 text-base mt-4"
            >
              {loading ? <LoadingSpinner size="sm" color="white" /> : 'Create Account'}
            </button>
          </form>

          <p className="mt-8 text-center text-sm text-on-surface-variant">
            Already have an account?{' '}
            <Link href="/login" className="font-medium text-primary hover:text-primary-container">
              Log in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
