import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Auth routes (accessible without a token, redirect to dashboard if already authed)
const authRoutes = ['/login', '/register', '/forgot-password', '/reset-password']

// BUG-021 fix: removed the ambiguous protectedRoutes list that included '/' as an entry.
// '/' as a startsWith check matches ALL paths, making the rest of the list redundant and
// confusing. Instead, we protect EVERYTHING except explicit auth routes — which is the
// correct behaviour for a finance app anyway.
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Check for auth token in cookies (set on login)
  const token = request.cookies.get('finora_token')?.value

  const isAuthRoute = authRoutes.some((route) => pathname.startsWith(route))

  // All non-auth routes require authentication
  const isProtected = !isAuthRoute

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
