'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Search,
  MessageSquare,
  Bookmark,
  LayoutDashboard,
  User,
  Settings,
  HelpCircle,
  FileText,
  Clock,
  TrendingUp,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface SidebarItem {
  title: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string | number;
}

const mainItems: SidebarItem[] = [
  {
    title: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
  },
  {
    title: 'Search Laws',
    href: '/search',
    icon: Search,
  },
  {
    title: 'Chat Q&A',
    href: '/chat',
    icon: MessageSquare,
  },
  {
    title: 'Bookmarks',
    href: '/bookmarks',
    icon: Bookmark,
  },
];

const secondaryItems: SidebarItem[] = [
  {
    title: 'Recent Activity',
    href: '/activity',
    icon: Clock,
  },
  {
    title: 'Usage Stats',
    href: '/usage',
    icon: TrendingUp,
  },
  {
    title: 'Documents',
    href: '/documents',
    icon: FileText,
  },
];

const bottomItems: SidebarItem[] = [
  {
    title: 'Profile',
    href: '/profile',
    icon: User,
  },
  {
    title: 'Settings',
    href: '/settings',
    icon: Settings,
  },
  {
    title: 'Help & Support',
    href: '/help',
    icon: HelpCircle,
  },
];

interface SidebarProps {
  className?: string;
  collapsed?: boolean;
}

export function Sidebar({ className, collapsed = false }: SidebarProps) {
  const pathname = usePathname();

  return (
    <aside
      className={cn(
        'flex flex-col h-full bg-background border-r transition-all duration-300',
        collapsed ? 'w-16' : 'w-64',
        className
      )}
    >
      {/* Main Navigation */}
      <div className="flex-1 py-4">
        <nav className="space-y-1 px-3">
          <div className={cn('mb-4', collapsed ? 'px-0' : 'px-2')}>
            <h2
              className={cn(
                'text-xs font-semibold text-muted-foreground uppercase tracking-wider',
                collapsed && 'text-center'
              )}
            >
              {collapsed ? '•' : 'Main'}
            </h2>
          </div>
          {mainItems.map((item) => (
            <SidebarLink
              key={item.href}
              item={item}
              isActive={pathname === item.href}
              collapsed={collapsed}
            />
          ))}
        </nav>

        {/* Secondary Navigation */}
        <nav className="mt-8 space-y-1 px-3">
          <div className={cn('mb-4', collapsed ? 'px-0' : 'px-2')}>
            <h2
              className={cn(
                'text-xs font-semibold text-muted-foreground uppercase tracking-wider',
                collapsed && 'text-center'
              )}
            >
              {collapsed ? '•' : 'Activity'}
            </h2>
          </div>
          {secondaryItems.map((item) => (
            <SidebarLink
              key={item.href}
              item={item}
              isActive={pathname === item.href}
              collapsed={collapsed}
            />
          ))}
        </nav>
      </div>

      {/* Bottom Navigation */}
      <div className="py-4 border-t">
        <nav className="space-y-1 px-3">
          {bottomItems.map((item) => (
            <SidebarLink
              key={item.href}
              item={item}
              isActive={pathname === item.href}
              collapsed={collapsed}
            />
          ))}
        </nav>
      </div>
    </aside>
  );
}

interface SidebarLinkProps {
  item: SidebarItem;
  isActive: boolean;
  collapsed: boolean;
}

function SidebarLink({ item, isActive, collapsed }: SidebarLinkProps) {
  const Icon = item.icon;

  return (
    <Link
      href={item.href}
      className={cn(
        'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
        isActive
          ? 'bg-accent text-accent-foreground'
          : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
        collapsed && 'justify-center px-2'
      )}
      title={collapsed ? item.title : undefined}
    >
      <Icon className="h-5 w-5 flex-shrink-0" />
      {!collapsed && (
        <>
          <span className="flex-1">{item.title}</span>
          {item.badge && (
            <span className="ml-auto flex h-5 min-w-[20px] items-center justify-center rounded-full bg-primary px-1.5 text-[10px] font-medium text-primary-foreground">
              {item.badge}
            </span>
          )}
        </>
      )}
    </Link>
  );
}