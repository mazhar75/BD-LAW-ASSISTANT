'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/Card';
import { useToast } from '@/components/providers/ToastProvider';
import { authService } from '@/lib/api/services/auth.service';
import { useAuthStore } from '@/store/authStore';
import { Eye, EyeOff, User, Mail, Lock, AlertCircle, CheckCircle, UserPlus } from 'lucide-react';
import { ApiError } from '@/types/errors';

const passwordStrengthRegex = {
  uppercase: /[A-Z]/,
  lowercase: /[a-z]/,
  number: /[0-9]/,
  special: /[!@#$%^&*]/
};

const registerSchema = z.object({
  username: z.string()
    .min(3, 'Username must be at least 3 characters')
    .max(20, 'Username must be less than 20 characters')
    .regex(/^[a-zA-Z0-9_-]+$/, 'Username can only contain letters, numbers, underscores and hyphens'),
  email: z.string().email('Invalid email address'),
  password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .refine(val => passwordStrengthRegex.uppercase.test(val), 'Password must contain an uppercase letter')
    .refine(val => passwordStrengthRegex.lowercase.test(val), 'Password must contain a lowercase letter')
    .refine(val => passwordStrengthRegex.number.test(val), 'Password must contain a number')
    .refine(val => passwordStrengthRegex.special.test(val), 'Password must contain a special character'),
  confirmPassword: z.string(),
  acceptTerms: z.boolean().refine(val => val === true, 'You must accept the terms and conditions')
}).refine(data => data.password === data.confirmPassword, {
  message: "Passwords don&apos;t match",
  path: ["confirmPassword"]
});

type RegisterFormData = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const router = useRouter();
  const { showToast } = useToast();
  const setUser = useAuthStore((state) => state.setUser);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [registrationStatus, setRegistrationStatus] = useState<{
    type: 'success' | 'error' | null;
    message: string;
  }>({ type: null, message: '' });
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
    setError,
    watch
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      acceptTerms: false
    }
  });

  const password = watch('password');

  const checkPasswordStrength = (value: string) => {
    setPasswordStrength({
      length: value.length >= 8,
      uppercase: passwordStrengthRegex.uppercase.test(value),
      lowercase: passwordStrengthRegex.lowercase.test(value),
      number: passwordStrengthRegex.number.test(value),
      special: passwordStrengthRegex.special.test(value)
    });
  };

  const onSubmit = async (data: RegisterFormData) => {
    try {
      setIsLoading(true);

      // Log the request data to debug
      const requestData = {
        username: data.username,
        email: data.email,
        password: data.password,
        fullName: data.username,  // Use username as fullName for now
        acceptTerms: data.acceptTerms
      };
      console.log('Sending registration request:', requestData);

      const response = await authService.register(requestData);

      if (response.success) {
        // Store the user data (auto-login after registration)
        setUser(response.data.user);

        // Set inline success message
        setRegistrationStatus({
          type: 'success',
          message: '✅ Registration successful! Logging you in...'
        });

        // Show toast notification
        showToast({
          title: 'Registration Successful! 🎉',
          description: 'Your account has been created. Redirecting to dashboard...',
          type: 'success',
          duration: 5000
        });

        // Redirect to dashboard after 2 seconds (user is already logged in)
        setTimeout(() => {
          router.replace('/dashboard');
        }, 2000);
      }
    } catch (error: any) {
      console.error('Registration error:', error);

      // Log detailed error information
      if (error.response) {
        console.error('Error response:', {
          status: error.response.status,
          data: error.response.data,
          headers: error.response.headers
        });
      } else if (error.request) {
        console.error('No response received:', error.request);
      } else {
        console.error('Error details:', error.message);
      }

      const apiError = error as ApiError;

      if (apiError.response?.status === 409) {
        if (apiError.response.data?.field === 'email') {
          setError('email', { message: 'Email already exists' });
        } else if (apiError.response.data?.field === 'username') {
          setError('username', { message: 'Username already taken' });
        }
      } else if (apiError.response?.status === 400) {
        // Handle validation errors
        const errorData = apiError.response.data;
        const errorMessage = errorData?.message || errorData?.error || 'Validation failed';

        // Set inline error message
        setRegistrationStatus({
          type: 'error',
          message: `❌ ${errorMessage}`
        });

        // Show toast notification
        showToast({
          title: 'Validation Error',
          description: errorMessage,
          type: 'error',
          duration: 5000
        });

        // Check for field-specific errors
        if (errorData?.errors) {
          Object.entries(errorData.errors).forEach(([field, msg]: [string, any]) => {
            if (field in errors) {
              setError(field as any, { message: msg });
            }
          });
        }
      } else {
        const errorMessage = apiError.response?.data?.message || apiError.message || 'An error occurred during registration';

        // Set inline error message
        setRegistrationStatus({
          type: 'error',
          message: `❌ ${errorMessage}`
        });

        // Show toast notification
        showToast({
          title: 'Registration Failed',
          description: errorMessage,
          type: 'error',
          duration: 5000
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12 bg-background">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold">Create Account</h1>
          <p className="mt-2 text-muted-foreground">
            Join BD Law Assistant to access legal resources
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Sign Up</CardTitle>
            <CardDescription>
              Fill in your information to create a new account
            </CardDescription>
          </CardHeader>

          <form onSubmit={handleSubmit(onSubmit)}>
            <CardContent className="space-y-4">
              {/* Registration Status Alert */}
              {registrationStatus.type && (
                <div
                  className={`p-3 rounded-md text-sm font-medium ${
                    registrationStatus.type === 'success'
                      ? 'bg-green-50 text-green-800 border border-green-200'
                      : 'bg-red-50 text-red-800 border border-red-200'
                  }`}
                >
                  {registrationStatus.message}
                </div>
              )}
              <div className="space-y-2">
                <label htmlFor="username" className="text-sm font-medium">
                  Username
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="username"
                    type="text"
                    placeholder="johndoe"
                    {...register('username')}
                    className="pl-10"
                    disabled={isLoading}
                  />
                </div>
                {errors.username && (
                  <p className="text-sm text-destructive flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    {errors.username.message}
                  </p>
                )}
              </div>

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

              <div className="space-y-2">
                <label htmlFor="password" className="text-sm font-medium">
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Create a strong password"
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
                  Confirm Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="confirmPassword"
                    type={showConfirmPassword ? 'text' : 'password'}
                    placeholder="Re-enter your password"
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

              <div className="space-y-2">
                <div className="flex items-start space-x-2">
                  <input
                    type="checkbox"
                    id="acceptTerms"
                    {...register('acceptTerms')}
                    className="h-4 w-4 rounded border-input focus:ring-2 focus:ring-primary mt-0.5"
                    disabled={isLoading}
                  />
                  <label htmlFor="acceptTerms" className="text-sm text-muted-foreground">
                    I agree to the{' '}
                    <Link href="/terms" className="text-primary hover:underline">
                      Terms and Conditions
                    </Link>
                    {' '}and{' '}
                    <Link href="/privacy" className="text-primary hover:underline">
                      Privacy Policy
                    </Link>
                  </label>
                </div>
                {errors.acceptTerms && (
                  <p className="text-sm text-destructive flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    {errors.acceptTerms.message}
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
                <UserPlus className="h-4 w-4 mr-2" />
                Create Account
              </Button>

              <p className="text-center text-sm text-muted-foreground">
                Already have an account?{' '}
                <Link href="/login" className="text-primary hover:underline font-medium">
                  Sign in
                </Link>
              </p>
            </CardFooter>
          </form>
        </Card>
      </div>
    </div>
  );
}