import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const { accessToken, refreshToken } = await request.json();

    if (!accessToken || !refreshToken) {
      return NextResponse.json(
        { error: 'Missing tokens' },
        { status: 400 }
      );
    }

    const response = NextResponse.json({ success: true });

    // Set cookies in the response headers
    // This ensures they're sent to the browser and available to middleware
    response.cookies.set('bd_law_access_token', accessToken, {
      httpOnly: false, // Allow client-side access
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 60 * 60 * 24, // 1 day
      path: '/'
    });

    response.cookies.set('bd_law_refresh_token', refreshToken, {
      httpOnly: false, // Allow client-side access
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 60 * 60 * 24 * 7, // 7 days
      path: '/'
    });

    return response;
  } catch (error) {
    console.error('Error setting cookies:', error);
    return NextResponse.json(
      { error: 'Failed to set cookies' },
      { status: 500 }
    );
  }
}
