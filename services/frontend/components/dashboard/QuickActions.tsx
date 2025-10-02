'use client';

import { Button } from '@/components/ui/Button';
import { Search, MessageSquarePlus, FileText, BookOpen, Settings, HelpCircle } from 'lucide-react';
import Link from 'next/link';

const actions = [
  {
    title: 'New Search',
    description: 'Search laws',
    icon: Search,
    href: '/search',
    color: 'text-blue-600'
  },
  {
    title: 'Start Chat',
    description: 'Ask questions',
    icon: MessageSquarePlus,
    href: '/chat',
    color: 'text-green-600'
  },
  {
    title: 'Bookmarks',
    description: 'Saved laws',
    icon: BookOpen,
    href: '/bookmarks',
    color: 'text-purple-600'
  },
  {
    title: 'Documents',
    description: 'Export history',
    icon: FileText,
    href: '/documents',
    color: 'text-orange-600'
  },
  {
    title: 'Settings',
    description: 'Preferences',
    icon: Settings,
    href: '/settings',
    color: 'text-gray-600'
  },
  {
    title: 'Help',
    description: 'Get support',
    icon: HelpCircle,
    href: '/help',
    color: 'text-indigo-600'
  }
];

export function QuickActions() {
  return (
    <div className="grid grid-cols-2 gap-3">
      {actions.map((action) => {
        const Icon = action.icon;
        return (
          <Link key={action.href} href={action.href}>
            <Button variant="outline" className="w-full h-auto p-4 flex flex-col items-center gap-2">
              <Icon className={`h-5 w-5 ${action.color}`} />
              <div className="text-center">
                <p className="text-sm font-medium">{action.title}</p>
                <p className="text-xs text-gray-500">{action.description}</p>
              </div>
            </Button>
          </Link>
        );
      })}
    </div>
  );
}