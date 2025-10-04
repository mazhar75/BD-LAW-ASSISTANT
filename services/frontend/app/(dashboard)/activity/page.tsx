'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { Clock, Search, MessageSquare, Bookmark, Eye } from 'lucide-react';
import { userService } from '@/lib/api/services/user.service';

interface ActivityItem {
  id: string;
  type: 'search' | 'chat' | 'bookmark' | 'view' | 'other';
  title: string;
  description: string;
  timestamp: string;
}

export default function ActivityPage() {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadActivities();
  }, []);

  const loadActivities = async () => {
    try {
      setIsLoading(true);
      const response = await userService.getUsage();
      const usageData = response?.usage || [];

      console.log('[Activity] Loaded usage data:', usageData.length, 'records');

      // Transform usage data to activities
      const transformedActivities = usageData.map((u: any, index: number) => {
        let type: ActivityItem['type'] = 'other';
        let title = 'API Request';
        let description = u.endpoint;

        if (u.endpoint?.includes('/api/rag/search')) {
          type = 'search';
          title = `Searched for "${u.query || 'legal documents'}"`;
          description = `Search in legal database`;
        } else if (u.endpoint?.includes('/api/rag/query')) {
          type = 'chat';
          title = `Asked: "${u.query || 'legal question'}"`;
          description = `Legal question in chat`;
        } else if (u.endpoint?.includes('/api/bookmarks')) {
          type = 'bookmark';
          title = 'Bookmark action';
          description = 'Managed bookmarks';
        } else if (u.endpoint?.includes('/api/user/')) {
          // Skip internal user API calls
          return null;
        }

        return {
          id: `${u.date}-${index}`,
          type,
          title,
          description,
          timestamp: u.date
        };
      }).filter(Boolean) as ActivityItem[];

      console.log('[Activity] Transformed to', transformedActivities.length, 'activities');
      setActivities(transformedActivities);
    } catch (error) {
      console.error('Failed to load activities:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'search': return <Search className="h-5 w-5 text-blue-600" />;
      case 'chat': return <MessageSquare className="h-5 w-5 text-green-600" />;
      case 'bookmark': return <Bookmark className="h-5 w-5 text-yellow-600" />;
      case 'view': return <Eye className="h-5 w-5 text-purple-600" />;
      default: return <Clock className="h-5 w-5 text-gray-600" />;
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Recent Activity</h1>
        <p className="mt-2 text-muted-foreground">
          Your recent interactions with BD Law Assistant
        </p>
      </div>

      <div className="space-y-3">
        {isLoading ? (
          <>
            {[1, 2, 3, 4, 5].map((i) => (
              <Card key={i} className="p-4">
                <div className="flex items-start gap-4">
                  <Skeleton className="h-10 w-10 rounded-lg" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-5 w-3/4" />
                    <Skeleton className="h-4 w-1/2" />
                    <Skeleton className="h-3 w-20" />
                  </div>
                </div>
              </Card>
            ))}
          </>
        ) : activities.length === 0 ? (
          <Card className="p-12">
            <div className="text-center">
              <Clock className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium mb-2">No Activity Yet</h3>
              <p className="text-muted-foreground">
                Your activity will appear here as you use the application
              </p>
            </div>
          </Card>
        ) : (
          activities.map((activity) => (
            <Card key={activity.id} className="p-4">
              <div className="flex items-start gap-4">
                <div className="p-2 bg-muted rounded-lg">
                  {getIcon(activity.type)}
                </div>
                <div className="flex-1">
                  <h3 className="font-medium">{activity.title}</h3>
                  <p className="text-sm text-muted-foreground mt-1">
                    {activity.description}
                  </p>
                  <p className="text-xs text-muted-foreground mt-2">
                    {formatTime(activity.timestamp)}
                  </p>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
