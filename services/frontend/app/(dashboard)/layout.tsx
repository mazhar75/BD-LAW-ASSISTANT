'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';
import { MobileNav } from '@/components/layout/MobileNav';
export default function DashboardLayout({
  children
}: {
  children: React.ReactNode;
}) {

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-background">
        <Header />

        <div className="flex">
          <Sidebar />

          <main className="flex-1 transition-all duration-300 lg:ml-64">
            <div className="container mx-auto px-4 py-8">
              {children}
            </div>
          </main>
        </div>

        <MobileNav />
      </div>
    </ProtectedRoute>
  );
}