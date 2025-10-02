import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Define public paths that don't require authentication
const publicPaths = [
  '/',
  '/login',
  '/register',
  '/reset-password',
  '/verify-email',
  '/test-registration'
];

// Define protected paths that require authentication
const protectedPaths = [
  '/dashboard',
  '/profile',
  '/settings',
  '/chat'
];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Check if it's a public path
  const isPublicPath = publicPaths.some(path => pathname.startsWith(path));

  // Check if it's a protected path
  const isProtectedPath = protectedPaths.some(path => pathname.startsWith(path));

  // Get the access token from cookies
  const accessToken = request.cookies.get('bd_law_access_token')?.value;
  const refreshToken = request.cookies.get('bd_law_refresh_token')?.value;

  // If it's a protected path and user is not authenticated, redirect to login
  if (isProtectedPath && !accessToken && !refreshToken) {
    const url = new URL('/login', request.url);
    url.searchParams.set('redirect', pathname);
    return NextResponse.redirect(url);
  }

  // If user is authenticated and trying to access auth pages, redirect to dashboard
  if ((pathname === '/login' || pathname === '/register') && accessToken) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  // Continue with the request
  return NextResponse.next();
}

// Configure which routes the middleware should run on
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public files (public folder)
     */
    '/((?!api|_next/static|_next/image|favicon.ico|public).*)',
  ],
};