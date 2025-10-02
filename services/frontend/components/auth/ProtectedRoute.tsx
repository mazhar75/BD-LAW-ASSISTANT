'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: string[];
  redirectTo?: string;
}

export function ProtectedRoute({
  children,
  requiredRoles = [],
  redirectTo = '/login',
}: ProtectedRouteProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, isLoading } = useAuthStore();

  useEffect(() => {
    if (!isLoading) {
      // Check if user is not authenticated
      if (!isAuthenticated || !user) {
        // Save the current path to redirect back after login
        const returnUrl = encodeURIComponent(pathname);
        router.push(`${redirectTo}?returnUrl=${returnUrl}`);
        return;
      }

      // Check role-based access
      if (requiredRoles.length > 0 && user.roles) {
        const hasRequiredRole = requiredRoles.some((role) =>
          user.roles.includes(role)
        );

        if (!hasRequiredRole) {
          router.push('/unauthorized');
          return;
        }
      }

      // Check if email is verified (if required)
      if (!user.isEmailVerified) {
        router.push('/verify-email');
        return;
      }

      // Check if account is active
      if (!user.isActive) {
        router.push('/account-inactive');
        return;
      }
    }
  }, [isAuthenticated, user, isLoading, requiredRoles, router, pathname, redirectTo]);

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  // Don't render children until authentication is verified
  if (!isAuthenticated || !user) {
    return null;
  }

  return <>{children}</>;
}