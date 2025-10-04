'use client';

import { useEffect, useState } from 'react';
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
  const [hydrated, setHydrated] = useState(false);

  // Wait for Zustand to hydrate from localStorage
  useEffect(() => {
    setHydrated(true);
  }, []);

  useEffect(() => {
    // Don't check auth until hydrated
    if (!hydrated) {
      return;
    }

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

      // Optional: Check if email is verified
      // Uncomment if email verification is required
      // if (!user.isEmailVerified) {
      //   router.push('/verify-email');
      //   return;
      // }

      // Optional: Check if account is active
      // Uncomment if active account check is required
      // if (!user.isActive) {
      //   router.push('/account-inactive');
      //   return;
      // }
    }
  }, [hydrated, isAuthenticated, user, isLoading, requiredRoles, router, pathname, redirectTo]);

  // Show loading state while hydrating or loading
  if (!hydrated || isLoading) {
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