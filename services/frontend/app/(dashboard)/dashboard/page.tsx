'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { useAuthStore } from '@/store/authStore';
import { userService } from '@/lib/api/services/user.service';
import gatewayClient from '@/lib/api/client';
import { format } from 'date-fns';
import Link from 'next/link';
import {
  Search, MessageSquare, BookOpen, TrendingUp,
  FileText, Activity,
  ArrowRight, BarChart3
} from 'lucide-react';
import { ApiError } from '@/types/errors';

interface UsageData {
  totalSearches?: number;
  totalQuestions?: number;
  lawsViewed?: number;
  savedItems?: number;
  weeklySearches?: number;
  weeklyQuestions?: number;
  weeklyTime?: string;
  recentActivity?: Array<{
    type: string;
    title: string;
    description: string;
    timestamp: string;
  }>;
}

export default function DashboardPage() {
  const user = useAuthStore((state) => state.user);
  const [usage, setUsage] = useState<UsageData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchUsageData();
  }, []);

  const fetchUsageData = async () => {
    try {
      setIsLoading(true);

      // Fetch usage statistics
      const usageResponse = await userService.getUsage();

      // Fetch bookmark count
      let bookmarkCount = 0;
      try {
        const bookmarkResponse = await gatewayClient.get('/api/bookmarks/count');
        console.log('[Dashboard] Bookmark count response:', {
          data: bookmarkResponse.data,
          type: typeof bookmarkResponse.data,
          fullResponse: bookmarkResponse
        });
        // The endpoint returns a Long directly, so data is the number
        bookmarkCount = typeof bookmarkResponse.data === 'number' ? bookmarkResponse.data : 0;
        console.log('[Dashboard] Final bookmark count:', bookmarkCount);
      } catch (err) {
        console.error('[Dashboard] Failed to fetch bookmark count:', err);
        // Try alternative: count from getAll if count endpoint fails
        try {
          const allBookmarks = await gatewayClient.get('/api/bookmarks?page=0&size=1');
          console.log('[Dashboard] Bookmark page response:', allBookmarks.data);
          bookmarkCount = allBookmarks.data?.totalElements || 0;
          console.log('[Dashboard] Bookmark count from page:', bookmarkCount);
        } catch (err2) {
          console.error('[Dashboard] Failed to fetch bookmarks page:', err2);
        }
      }

      // Transform backend data to dashboard format
      const summary = usageResponse?.summary || {};
      const usageData = usageResponse?.usage || [];
      const totalRequests = summary.totalRequests || 0;

      console.log('[Dashboard] Processing usage data:', {
        totalRequests,
        usageRecords: usageData.length,
        endpoints: usageData.map((u: any) => u.endpoint)
      });

      // Calculate metrics from usage data
      // Note: Endpoints are logged with /api prefix (e.g., /api/rag/search)
      const searchEndpoints = usageData.filter((u: any) =>
        u.endpoint?.includes('/api/rag/search')
      );
      const searchCount = searchEndpoints.length;
      console.log('[Dashboard] Search count:', searchCount, 'from endpoints:', searchEndpoints.map((u: any) => u.endpoint));

      const chatEndpoints = usageData.filter((u: any) =>
        u.endpoint?.includes('/api/rag/query') // RAG query is used for chat
      );
      const chatCount = chatEndpoints.length;
      console.log('[Dashboard] Chat count:', chatCount, 'from endpoints:', chatEndpoints.map((u: any) => u.endpoint));

      const lawsViewedCount = usageData.filter((u: any) =>
        u.endpoint?.includes('/api/laws/') ||
        u.endpoint?.includes('/api/documents/') ||
        u.endpoint?.includes('/api/rag/query') || // RAG queries also count as viewing laws
        u.endpoint?.includes('/api/rag/search') // Search also counts as viewing
      ).length;
      console.log('[Dashboard] Laws viewed count:', lawsViewedCount);

      // Calculate weekly stats (last 7 days)
      const weekAgo = new Date();
      weekAgo.setDate(weekAgo.getDate() - 7);

      const weeklyData = usageData.filter((u: any) =>
        new Date(u.date) >= weekAgo
      );

      const weeklySearches = weeklyData.filter((u: any) =>
        u.endpoint?.includes('/api/rag/search')
      ).length;

      const weeklyChats = weeklyData.filter((u: any) =>
        u.endpoint?.includes('/api/rag/query')
      ).length;

      // Calculate time spent (sum of response times)
      const totalTimeMs = weeklyData.reduce((sum: number, u: any) =>
        sum + (u.responseTimeMs || 0), 0
      );
      const totalTimeMinutes = Math.round(totalTimeMs / 1000 / 60);
      const hours = Math.floor(totalTimeMinutes / 60);
      const minutes = totalTimeMinutes % 60;
      const weeklyTime = hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;

      // Transform recent activity
      const recentActivity = usageData.slice(0, 10).map((u: any) => {
        let type = 'other';
        let title = 'API Request';
        let description = u.endpoint;

        if (u.endpoint?.includes('/api/rag/search')) {
          type = 'search';
          title = 'Searched Laws';
          description = u.query || 'Legal document search';
        } else if (u.endpoint?.includes('/api/rag/query')) {
          type = 'question';
          title = 'Asked Question';
          description = u.query || 'Legal question in chat';
        } else if (u.endpoint?.includes('/api/bookmarks')) {
          type = 'view';
          title = 'Bookmarks';
          description = 'Accessed bookmarks';
        } else if (u.endpoint?.includes('/api/user/')) {
          // Don't show internal user API calls
          return null;
        }

        return {
          type,
          title,
          description,
          timestamp: u.date
        };
      }).filter(Boolean); // Remove null entries

      setUsage({
        totalSearches: searchCount,
        totalQuestions: chatCount,
        lawsViewed: lawsViewedCount,
        savedItems: bookmarkCount,
        weeklySearches,
        weeklyQuestions: weeklyChats,
        weeklyTime,
        recentActivity
      });
    } catch (error) {
      console.error('Failed to fetch usage data:', error);
      const apiError = error as ApiError;
      console.error('API Error:', apiError.message);
    } finally {
      setIsLoading(false);
    }
  };

  const stats = [
    {
      title: 'Total Requests',
      value: usage?.totalSearches || 0,
      icon: Search,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
      description: 'All-time API requests'
    },
    {
      title: 'Questions Asked',
      value: usage?.totalQuestions || 0,
      icon: MessageSquare,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
      description: 'Chat conversations'
    },
    {
      title: 'Laws Viewed',
      value: usage?.lawsViewed || 0,
      icon: BookOpen,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
      description: 'Documents accessed'
    },
    {
      title: 'Saved Bookmarks',
      value: usage?.savedItems || 0,
      icon: FileText,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
      description: 'Bookmarked items'
    }
  ];

  const recentActivity = usage?.recentActivity || [];
  const quickActions = [
    { title: 'Search Laws', icon: Search, href: '/search', color: 'text-blue-600' },
    { title: 'Ask Question', icon: MessageSquare, href: '/chat', color: 'text-green-600' },
    { title: 'View Bookmarks', icon: BookOpen, href: '/bookmarks', color: 'text-purple-600' },
    { title: 'Usage Stats', icon: BarChart3, href: '/analytics', color: 'text-orange-600' }
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">
          Welcome back, {user?.username || 'User'}!
        </h1>
        <p className="text-muted-foreground">
          {format(new Date(), 'EEEE, MMMM dd, yyyy')}
        </p>
      </div>

      {/* Statistics Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, index) => (
          <Card key={index}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {stat.title}
              </CardTitle>
              <div className={`${stat.bgColor} p-2 rounded-lg`}>
                <stat.icon className={`h-4 w-4 ${stat.color}`} />
              </div>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <Skeleton className="h-8 w-20" />
              ) : (
                <>
                  <div className="text-2xl font-bold">{stat.value}</div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {stat.description}
                  </p>
                </>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Recent Activity */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>Your latest actions and searches</CardDescription>
              </div>
              <Link href="/activity">
                <Button variant="ghost" size="sm">
                  View All
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : recentActivity.length > 0 ? (
              <div className="space-y-3">
                {recentActivity.slice(0, 5).map((activity, index: number) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 rounded-lg hover:bg-muted transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${
                        activity.type === 'search' ? 'bg-blue-100' :
                        activity.type === 'question' ? 'bg-green-100' :
                        'bg-purple-100'
                      }`}>
                        {activity.type === 'search' ? (
                          <Search className="h-4 w-4 text-blue-600" />
                        ) : activity.type === 'question' ? (
                          <MessageSquare className="h-4 w-4 text-green-600" />
                        ) : (
                          <BookOpen className="h-4 w-4 text-purple-600" />
                        )}
                      </div>
                      <div>
                        <p className="text-sm font-medium">{activity.title}</p>
                        <p className="text-xs text-muted-foreground">
                          {activity.description}
                        </p>
                      </div>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {format(new Date(activity.timestamp), 'MMM dd, HH:mm')}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <Activity className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
                <p className="text-sm text-muted-foreground">No recent activity</p>
                <Link href="/search">
                  <Button className="mt-4" size="sm">
                    Start Searching
                  </Button>
                </Link>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Jump to frequently used features</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-2">
              {quickActions.map((action, index) => (
                <Link key={index} href={action.href}>
                  <Button
                    variant="outline"
                    className="w-full justify-start hover:bg-muted"
                  >
                    <action.icon className={`h-4 w-4 mr-2 ${action.color}`} />
                    {action.title}
                  </Button>
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Insights Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Weekly Insights</CardTitle>
              <CardDescription>Your usage patterns this week</CardDescription>
            </div>
            <Link href="/analytics">
              <Button variant="outline" size="sm">
                <BarChart3 className="h-4 w-4 mr-2" />
                View Analytics
              </Button>
            </Link>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-32 w-full" />
          ) : (
            <div className="grid gap-4 md:grid-cols-3">
              <div className="text-center">
                <div className="text-3xl font-bold text-primary">
                  {usage?.weeklySearches || 0}
                </div>
                <p className="text-sm text-muted-foreground">Searches this week</p>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600">
                  {usage?.weeklyQuestions || 0}
                </div>
                <p className="text-sm text-muted-foreground">Questions asked</p>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-purple-600">
                  {usage?.weeklyTime || '0h'}
                </div>
                <p className="text-sm text-muted-foreground">Time spent</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}