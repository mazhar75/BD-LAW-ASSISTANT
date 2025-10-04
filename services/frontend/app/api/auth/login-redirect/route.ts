import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = request.nextUrl;
    const accessToken = searchParams.get('accessToken');
    const refreshToken = searchParams.get('refreshToken');
    const redirect = searchParams.get('redirect') || '/dashboard';

    if (!accessToken || !refreshToken) {
      return NextResponse.redirect(new URL('/login?error=missing_tokens', request.url));
    }

    // Create redirect response
    const response = NextResponse.redirect(new URL(redirect, request.url));

    // Set cookies in the redirect response
    response.cookies.set('bd_law_access_token', accessToken, {
      httpOnly: false,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 60 * 60 * 24, // 1 day
      path: '/'
    });

    response.cookies.set('bd_law_refresh_token', refreshToken, {
      httpOnly: false,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 60 * 60 * 24 * 7, // 7 days
      path: '/'
    });

    console.log('[Login Redirect] Setting cookies and redirecting to:', redirect);

    return response;
  } catch (error) {
    console.error('Error in login redirect:', error);
    return NextResponse.redirect(new URL('/login?error=redirect_failed', request.url));
  }
}
