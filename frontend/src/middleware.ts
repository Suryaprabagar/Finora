import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Routes that require authentication
const protectedRoutes = [
  '/',
  '/transactions',
  '/income',
  '/expenses',
  '/budget',
  '/bank-accounts',
  '/credit-cards',
  '/investments',
  '/loans',
  '/assets',
  '/insurance',
  '/bills',
  '/goals',
  '/reports',
  '/settings',
]

// Auth routes (redirect to dashboard if already authenticated)
const authRoutes = ['/login', '/register', '/forgot-password', '/reset-password']

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Check for auth token in cookies (we'll set it on login)
  const token = request.cookies.get('finora_token')?.value

  const isProtected = protectedRoutes.some(
    (route) => pathname === route || pathname.startsWith(`${route}/`)
  )
  const isAuthRoute = authRoutes.some((route) => pathname.startsWith(route))

  if (isProtected && !token) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  if (isAuthRoute && token) {
    return NextResponse.redirect(new URL('/', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico|public).*)'],
}
