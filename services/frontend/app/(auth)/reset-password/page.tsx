'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/Card';
import { useToast } from '@/components/ui/Toast';
import { authService } from '@/lib/api/services/auth.service';
import { Mail, AlertCircle, ArrowLeft, Send, CheckCircle } from 'lucide-react';
import { ApiError } from '@/types/errors';

const resetRequestSchema = z.object({
  email: z.string().email('Invalid email address')
});

type ResetRequestFormData = z.infer<typeof resetRequestSchema>;

export default function ResetPasswordPage() {
  const { showToast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const [sentEmail, setSentEmail] = useState('');

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError
  } = useForm<ResetRequestFormData>({
    resolver: zodResolver(resetRequestSchema)
  });

  const onSubmit = async (data: ResetRequestFormData) => {
    try {
      setIsLoading(true);
      const response = await authService.requestPasswordReset(data.email);

      if (response.success) {
        setSentEmail(data.email);
        setEmailSent(true);
        showToast({
          title: 'Email Sent',
          description: 'Check your email for password reset instructions',
          type: 'success'
        });
      }
    } catch (error) {
      console.error('Password reset request error:', error);
      const apiError = error as ApiError;

      if (apiError.response?.status === 404) {
        setError('email', { message: 'No account found with this email' });
      } else {
        showToast({
          title: 'Request Failed',
          description: apiError.response?.data?.message || apiError.message || 'Unable to process password reset request',
          type: 'error'
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const resendEmail = async () => {
    if (!sentEmail) return;

    try {
      setIsLoading(true);
      await authService.requestPasswordReset(sentEmail);
      showToast({
        title: 'Email Resent',
        description: 'Password reset instructions have been sent again',
        type: 'success'
      });
    } catch {
      showToast({
        title: 'Resend Failed',
        description: 'Unable to resend email. Please try again later.',
        type: 'error'
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (emailSent) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4 py-12 bg-background">
        <div className="w-full max-w-md space-y-8">
          <Card>
            <CardHeader className="text-center">
              <div className="mx-auto w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mb-4">
                <CheckCircle className="h-6 w-6 text-green-600" />
              </div>
              <CardTitle>Check Your Email</CardTitle>
              <CardDescription className="mt-2">
                We&apos;ve sent password reset instructions to:
                <br />
                <span className="font-medium text-foreground">{sentEmail}</span>
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-4">
              <div className="bg-muted p-4 rounded-lg">
                <p className="text-sm text-muted-foreground">
                  Didn&apos;t receive the email? Check your spam folder or click below to resend.
                </p>
              </div>

              <Button
                onClick={resendEmail}
                variant="outline"
                className="w-full"
                disabled={isLoading}
                loading={isLoading}
              >
                <Send className="h-4 w-4 mr-2" />
                Resend Email
              </Button>
            </CardContent>

            <CardFooter className="flex justify-center">
              <Link
                href="/login"
                className="text-sm text-primary hover:underline flex items-center gap-1"
              >
                <ArrowLeft className="h-3 w-3" />
                Back to Sign In
              </Link>
            </CardFooter>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12 bg-background">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold">Reset Password</h1>
          <p className="mt-2 text-muted-foreground">
            Enter your email to receive reset instructions
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Forgot your password?</CardTitle>
            <CardDescription>
              We&apos;ll send you an email with instructions to reset your password
            </CardDescription>
          </CardHeader>

          <form onSubmit={handleSubmit(onSubmit)}>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label htmlFor="email" className="text-sm font-medium">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="name@example.com"
                    {...register('email')}
                    className="pl-10"
                    disabled={isLoading}
                  />
                </div>
                {errors.email && (
                  <p className="text-sm text-destructive flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    {errors.email.message}
                  </p>
                )}
              </div>
            </CardContent>

            <CardFooter className="flex flex-col space-y-4">
              <Button
                type="submit"
                className="w-full"
                loading={isLoading}
                disabled={isLoading}
              >
                <Send className="h-4 w-4 mr-2" />
                Send Reset Instructions
              </Button>

              <Link
                href="/login"
                className="text-sm text-primary hover:underline flex items-center gap-1"
              >
                <ArrowLeft className="h-3 w-3" />
                Back to Sign In
              </Link>
            </CardFooter>
          </form>
        </Card>
      </div>
    </div>
  );
}