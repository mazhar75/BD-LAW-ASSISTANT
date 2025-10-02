'use client';

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useToast } from '@/components/ui/Toast';
import { authService } from '@/lib/api/services/auth.service';
import { CheckCircle, XCircle, Mail, RefreshCw, Home, LogIn } from 'lucide-react';
import { ApiError } from '@/types/errors';

function VerifyEmailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { showToast } = useToast();
  const [verificationStatus, setVerificationStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [errorMessage, setErrorMessage] = useState('');
  const [resending, setResending] = useState(false);
  const [email, setEmail] = useState('');

  const token = searchParams.get('token');
  const userEmail = searchParams.get('email');

  useEffect(() => {
    if (userEmail) {
      setEmail(userEmail);
    }

    if (token) {
      verifyEmail();
    } else {
      setVerificationStatus('error');
      setErrorMessage('No verification token provided');
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, userEmail]);

  const verifyEmail = async () => {
    if (!token) return;

    try {
      const response = await authService.verifyEmail(token);

      if (response.success) {
        setVerificationStatus('success');
        showToast({
          title: 'Email Verified',
          description: 'Your email has been successfully verified',
          type: 'info'
        });

        setTimeout(() => {
          router.push('/login?verified=true');
        }, 3000);
      }
    } catch (error) {
      setVerificationStatus('error');
      const apiError = error as ApiError;

      if (apiError.response?.status === 400) {
        setErrorMessage('This verification link has expired or is invalid');
      } else if (apiError.response?.status === 409) {
        setErrorMessage('This email has already been verified');
      } else {
        setErrorMessage(apiError.response?.data?.message || apiError.message || 'Verification failed. Please try again.');
      }
    }
  };

  const resendVerificationEmail = async () => {
    if (!email) {
      showToast({
        title: 'Email Required',
        description: 'Please provide your email to resend verification',
        type: 'error'
      });
      return;
    }

    try {
      setResending(true);
      const response = await authService.resendVerificationEmail(email);

      if (response.success) {
        showToast({
          title: 'Email Sent',
          description: 'A new verification email has been sent',
          type: 'info'
        });
      }
    } catch (error) {
      const apiError = error as ApiError;
      showToast({
        title: 'Resend Failed',
        description: apiError.response?.data?.message || apiError.message || 'Unable to resend verification email',
        type: 'error'
      });
    } finally {
      setResending(false);
    }
  };

  if (verificationStatus === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center px-4 py-12 bg-background">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mb-4 animate-pulse">
              <Mail className="h-6 w-6 text-blue-600" />
            </div>
            <CardTitle>Verifying Email</CardTitle>
            <CardDescription>
              Please wait while we verify your email address...
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (verificationStatus === 'success') {
    return (
      <div className="min-h-screen flex items-center justify-center px-4 py-12 bg-background">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mb-4">
              <CheckCircle className="h-6 w-6 text-green-600" />
            </div>
            <CardTitle>Email Verified!</CardTitle>
            <CardDescription>
              Your email has been successfully verified. You can now sign in to your account.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="bg-muted p-4 rounded-lg text-center">
              <p className="text-sm text-muted-foreground">
                Redirecting to login page in 3 seconds...
              </p>
            </div>
          </CardContent>
          <CardFooter>
            <Link href="/login" className="w-full">
              <Button className="w-full">
                <LogIn className="h-4 w-4 mr-2" />
                Sign In Now
              </Button>
            </Link>
          </CardFooter>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12 bg-background">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mb-4">
            <XCircle className="h-6 w-6 text-red-600" />
          </div>
          <CardTitle>Verification Failed</CardTitle>
          <CardDescription>
            {errorMessage}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {email && (
            <div className="bg-muted p-4 rounded-lg">
              <p className="text-sm text-muted-foreground">
                Email: <span className="font-medium text-foreground">{email}</span>
              </p>
            </div>
          )}

          <Button
            onClick={resendVerificationEmail}
            variant="outline"
            className="w-full"
            disabled={resending || !email}
            loading={resending}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Resend Verification Email
          </Button>
        </CardContent>
        <CardFooter className="flex flex-col space-y-2">
          <Link href="/login" className="w-full">
            <Button variant="default" className="w-full">
              <LogIn className="h-4 w-4 mr-2" />
              Go to Sign In
            </Button>
          </Link>
          <Link href="/" className="w-full">
            <Button variant="ghost" className="w-full">
              <Home className="h-4 w-4 mr-2" />
              Back to Home
            </Button>
          </Link>
        </CardFooter>
      </Card>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center px-4 py-12 bg-background">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle>Loading...</CardTitle>
          </CardHeader>
        </Card>
      </div>
    }>
      <VerifyEmailContent />
    </Suspense>
  );
}