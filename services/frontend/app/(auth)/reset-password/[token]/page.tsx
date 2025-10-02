'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/Card';
import { useToast } from '@/components/ui/Toast';
import { authService } from '@/lib/api/services/auth.service';
import { Lock, Eye, EyeOff, AlertCircle, CheckCircle, KeyRound } from 'lucide-react';
import { ApiError } from '@/types/errors';

const passwordStrengthRegex = {
  uppercase: /[A-Z]/,
  lowercase: /[a-z]/,
  number: /[0-9]/,
  special: /[!@#$%^&*]/
};

const resetPasswordSchema = z.object({
  password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .refine(val => passwordStrengthRegex.uppercase.test(val), 'Password must contain an uppercase letter')
    .refine(val => passwordStrengthRegex.lowercase.test(val), 'Password must contain a lowercase letter')
    .refine(val => passwordStrengthRegex.number.test(val), 'Password must contain a number')
    .refine(val => passwordStrengthRegex.special.test(val), 'Password must contain a special character'),
  confirmPassword: z.string()
}).refine(data => data.password === data.confirmPassword, {
  message: "Passwords don&apos;t match",
  path: ["confirmPassword"]
});

type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;

export default function ResetPasswordConfirmPage({
  params
}: {
  params: Promise<{ token: string }>
}) {
  const [token, setToken] = useState<string>('');
  const router = useRouter();
  const { showToast } = useToast();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [tokenValid, setTokenValid] = useState<boolean | null>(null);
  const [passwordStrength, setPasswordStrength] = useState({
    length: false,
    uppercase: false,
    lowercase: false,
    number: false,
    special: false
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch
  } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema)
  });

  const password = watch('password');

  useEffect(() => {
    params.then(({ token: paramToken }) => {
      setToken(paramToken);
    });
  }, [params]);

  useEffect(() => {
    if (token) {
      validateToken();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const validateToken = async () => {
    try {
      const response = await authService.validateResetToken(token);
      setTokenValid(response.valid);
    } catch {
      setTokenValid(false);
      showToast({
        title: 'Invalid Token',
        description: 'This password reset link is invalid or has expired',
        type: 'error'
      });
    }
  };

  const checkPasswordStrength = (value: string) => {
    setPasswordStrength({
      length: value.length >= 8,
      uppercase: passwordStrengthRegex.uppercase.test(value),
      lowercase: passwordStrengthRegex.lowercase.test(value),
      number: passwordStrengthRegex.number.test(value),
      special: passwordStrengthRegex.special.test(value)
    });
  };

  const onSubmit = async (data: ResetPasswordFormData) => {
    try {
      setIsLoading(true);
      const response = await authService.resetPassword({
        token: token,
        newPassword: data.password
      });

      if (response.success) {
        showToast({
          title: 'Password Reset Successful',
          description: 'Your password has been updated. You can now sign in.',
          type: 'success'
        });
        router.push('/login?reset=success');
      }
    } catch (error) {
      console.error('Password reset error:', error);
      const apiError = error as ApiError;

      if (apiError.response?.status === 400) {
        showToast({
          title: 'Reset Failed',
          description: 'This reset link has expired. Please request a new one.',
          type: 'error'
        });
        setTokenValid(false);
      } else {
        showToast({
          title: 'Reset Failed',
          description: apiError.response?.data?.message || apiError.message || 'Unable to reset password',
          type: 'error'
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  if (!token || tokenValid === null) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (tokenValid === false) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4 py-12 bg-background">
        <div className="w-full max-w-md">
          <Card>
            <CardHeader className="text-center">
              <div className="mx-auto w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mb-4">
                <AlertCircle className="h-6 w-6 text-red-600" />
              </div>
              <CardTitle>Invalid or Expired Link</CardTitle>
              <CardDescription className="mt-2">
                This password reset link is no longer valid. Please request a new one.
              </CardDescription>
            </CardHeader>

            <CardFooter className="flex flex-col space-y-4">
              <Link href="/reset-password" className="w-full">
                <Button className="w-full">
                  Request New Reset Link
                </Button>
              </Link>
              <Link
                href="/login"
                className="text-sm text-primary hover:underline"
              >
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
          <h1 className="text-3xl font-bold">Create New Password</h1>
          <p className="mt-2 text-muted-foreground">
            Enter your new password below
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Reset Your Password</CardTitle>
            <CardDescription>
              Choose a strong password to secure your account
            </CardDescription>
          </CardHeader>

          <form onSubmit={handleSubmit(onSubmit)}>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label htmlFor="password" className="text-sm font-medium">
                  New Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Enter new password"
                    {...register('password', {
                      onChange: (e) => checkPasswordStrength(e.target.value)
                    })}
                    className="pl-10 pr-10"
                    disabled={isLoading}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                    tabIndex={-1}
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
                {errors.password && (
                  <p className="text-sm text-destructive flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    {errors.password.message}
                  </p>
                )}

                {password && (
                  <div className="space-y-1 mt-2">
                    <p className="text-xs font-medium text-muted-foreground">Password strength:</p>
                    <div className="space-y-1">
                      <div className={`flex items-center gap-1 text-xs ${passwordStrength.length ? 'text-green-600' : 'text-muted-foreground'}`}>
                        <CheckCircle className={`h-3 w-3 ${passwordStrength.length ? 'opacity-100' : 'opacity-30'}`} />
                        At least 8 characters
                      </div>
                      <div className={`flex items-center gap-1 text-xs ${passwordStrength.uppercase ? 'text-green-600' : 'text-muted-foreground'}`}>
                        <CheckCircle className={`h-3 w-3 ${passwordStrength.uppercase ? 'opacity-100' : 'opacity-30'}`} />
                        One uppercase letter
                      </div>
                      <div className={`flex items-center gap-1 text-xs ${passwordStrength.lowercase ? 'text-green-600' : 'text-muted-foreground'}`}>
                        <CheckCircle className={`h-3 w-3 ${passwordStrength.lowercase ? 'opacity-100' : 'opacity-30'}`} />
                        One lowercase letter
                      </div>
                      <div className={`flex items-center gap-1 text-xs ${passwordStrength.number ? 'text-green-600' : 'text-muted-foreground'}`}>
                        <CheckCircle className={`h-3 w-3 ${passwordStrength.number ? 'opacity-100' : 'opacity-30'}`} />
                        One number
                      </div>
                      <div className={`flex items-center gap-1 text-xs ${passwordStrength.special ? 'text-green-600' : 'text-muted-foreground'}`}>
                        <CheckCircle className={`h-3 w-3 ${passwordStrength.special ? 'opacity-100' : 'opacity-30'}`} />
                        One special character (!@#$%^&*)
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <label htmlFor="confirmPassword" className="text-sm font-medium">
                  Confirm New Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="confirmPassword"
                    type={showConfirmPassword ? 'text' : 'password'}
                    placeholder="Re-enter new password"
                    {...register('confirmPassword')}
                    className="pl-10 pr-10"
                    disabled={isLoading}
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                    tabIndex={-1}
                  >
                    {showConfirmPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
                {errors.confirmPassword && (
                  <p className="text-sm text-destructive flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    {errors.confirmPassword.message}
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
                <KeyRound className="h-4 w-4 mr-2" />
                Reset Password
              </Button>

              <Link
                href="/login"
                className="text-sm text-primary hover:underline"
              >
                Back to Sign In
              </Link>
            </CardFooter>
          </form>
        </Card>
      </div>
    </div>
  );
}