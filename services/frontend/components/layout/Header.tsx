'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Menu, X, Search, User, LogOut, Settings, BookOpen } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { useAuthStore } from '@/store/authStore';

export function Header() {
  const router = useRouter();
  const { user, isAuthenticated, clearAuth } = useAuthStore();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const handleLogout = async () => {
    try {
      // Call backend logout endpoint
      await fetch('/api/auth/logout', { method: 'POST' });
    } catch (error) {
      console.error('Logout API error:', error);
    } finally {
      // Clear auth state and cookies
      clearAuth();
      // Clear localStorage
      localStorage.removeItem('auth-storage');
      // Redirect to login
      router.push('/login');
    }
  };

  return (
    <header className="sticky top-0 z-40 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          {/* Logo and Brand */}
          <div className="flex items-center gap-6">
            <Link href="/" className="flex items-center gap-2">
              <BookOpen className="h-6 w-6 text-primary" />
              <span className="text-xl font-semibold">BD Law Assistant</span>
            </Link>

            {/* Desktop Navigation */}
            {isAuthenticated && (
              <nav className="hidden md:flex items-center gap-6">
                <Link
                  href="/search"
                  className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                >
                  Search Laws
                </Link>
                <Link
                  href="/chat"
                  className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                >
                  Chat Q&A
                </Link>
                <Link
                  href="/bookmarks"
                  className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                >
                  Bookmarks
                </Link>
                <Link
                  href="/dashboard"
                  className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                >
                  Dashboard
                </Link>
              </nav>
            )}
          </div>

          {/* Right Section */}
          <div className="flex items-center gap-4">
            {/* Search Button */}
            {isAuthenticated && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => router.push('/search')}
                className="hidden md:flex"
              >
                <Search className="h-5 w-5" />
              </Button>
            )}

            {/* User Menu */}
            {isAuthenticated ? (
              <div className="relative">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className="rounded-full"
                >
                  <User className="h-5 w-5" />
                </Button>

                {/* User Dropdown */}
                {userMenuOpen && (
                  <>
                    <div
                      className="fixed inset-0 z-40"
                      onClick={() => setUserMenuOpen(false)}
                    />
                    <div className="absolute right-0 top-full mt-2 w-64 rounded-md border bg-popover p-1 shadow-lg z-50">
                      <div className="px-2 py-1.5 text-sm">
                        <p className="font-medium">{user?.fullName || user?.username}</p>
                        <p className="text-muted-foreground">{user?.email}</p>
                      </div>
                      <div className="h-px bg-border my-1" />
                      <Link
                        href="/profile"
                        className="flex items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-accent"
                        onClick={() => setUserMenuOpen(false)}
                      >
                        <User className="h-4 w-4" />
                        Profile
                      </Link>
                      <Link
                        href="/settings"
                        className="flex items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-accent"
                        onClick={() => setUserMenuOpen(false)}
                      >
                        <Settings className="h-4 w-4" />
                        Settings
                      </Link>
                      <div className="h-px bg-border my-1" />
                      <button
                        onClick={handleLogout}
                        className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-accent text-left"
                      >
                        <LogOut className="h-4 w-4" />
                        Logout
                      </button>
                    </div>
                  </>
                )}
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Button variant="ghost" onClick={() => router.push('/login')}>
                  Login
                </Button>
                <Button onClick={() => router.push('/register')}>
                  Sign Up
                </Button>
              </div>
            )}

            {/* Mobile Menu Button */}
            {isAuthenticated && (
              <Button
                variant="ghost"
                size="icon"
                className="md:hidden"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              >
                {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Mobile Navigation */}
      {isAuthenticated && mobileMenuOpen && (
        <div className="md:hidden border-t">
          <nav className="container mx-auto px-4 py-4 space-y-2">
            <Link
              href="/search"
              className="block px-3 py-2 text-sm font-medium rounded-md hover:bg-accent"
              onClick={() => setMobileMenuOpen(false)}
            >
              Search Laws
            </Link>
            <Link
              href="/chat"
              className="block px-3 py-2 text-sm font-medium rounded-md hover:bg-accent"
              onClick={() => setMobileMenuOpen(false)}
            >
              Chat Q&A
            </Link>
            <Link
              href="/bookmarks"
              className="block px-3 py-2 text-sm font-medium rounded-md hover:bg-accent"
              onClick={() => setMobileMenuOpen(false)}
            >
              Bookmarks
            </Link>
            <Link
              href="/dashboard"
              className="block px-3 py-2 text-sm font-medium rounded-md hover:bg-accent"
              onClick={() => setMobileMenuOpen(false)}
            >
              Dashboard
            </Link>
          </nav>
        </div>
      )}
    </header>
  );
}