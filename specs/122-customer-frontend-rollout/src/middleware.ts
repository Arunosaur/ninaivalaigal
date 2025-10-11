/**
 * Customer App Middleware
 * Enforces customer-only access and authentication
 */

import { NextRequest, NextResponse } from 'next/server';
import { getToken } from 'next-auth/jwt';

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow auth routes (login, signup) without token
  if (pathname.startsWith('/login') || pathname.startsWith('/signup')) {
    return NextResponse.next();
  }

  // Get JWT token from NextAuth
  const token = await getToken({
    req: request,
    secret: process.env.NEXTAUTH_SECRET,
  });

  // Require authentication for protected routes
  if (!token) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('callbackUrl', pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Enforce customer-only access
  if (token.role !== 'customer') {
    return NextResponse.json(
      {
        error: 'Unauthorized',
        message: 'Customer access only. Please contact support.',
      },
      { status: 403 }
    );
  }

  // Add user info to headers for downstream consumption
  const response = NextResponse.next();
  response.headers.set('x-user-id', token.id as string);
  response.headers.set('x-user-role', token.role as string);

  return response;
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!_next/static|_next/image|favicon.ico|public).*)',
  ],
};
