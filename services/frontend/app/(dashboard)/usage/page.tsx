'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { TrendingUp, Search, MessageSquare, Bookmark, Clock, FileText } from 'lucide-react';
import { userService } from '@/lib/api/services/user.service';
import gatewayClient from '@/lib/api/client';
import { format } from 'date-fns';

export default function UsagePage() {
  const [isLoading, setIsLoading] = useState(true);
  const [stats, setStats] = useState({
    totalSearches: 0,
    totalQuestions: 0,
    totalBookmarks: 0,
    totalTime: '0h',
    weeklySearches: 0,
    weeklyQuestions: 0,
    weeklyBookmarks: 0,
    todaySearches: 0,
    todayQuestions: 0,
    todayBookmarks: 0,
    todayTime: '0h',
  });
  const [dailyUsage, setDailyUsage] = useState<any[]>([]);

  useEffect(() => {
    fetchUsageStats();
  }, []);

  const fetchUsageStats = async () => {
    try {
      setIsLoading(true);

      // Fetch usage data
      const usageResponse = await userService.getUsage();
      const usageData = usageResponse?.usage || [];

      // Fetch bookmark count
      let bookmarkCount = 0;
      try {
        const bookmarkResponse = await gatewayClient.get('/api/bookmarks/count');
        bookmarkCount = typeof bookmarkResponse.data === 'number' ? bookmarkResponse.data : 0;
      } catch (err) {
        console.error('Failed to fetch bookmark count:', err);
      }

      // Calculate all-time stats
      const searchCount = usageData.filter((u: any) =>
        u.endpoint?.includes('/api/rag/search')
      ).length;

      const questionCount = usageData.filter((u: any) =>
        u.endpoint?.includes('/api/rag/query')
      ).length;

      // Calculate time spent
      const totalTimeMs = usageData.reduce((sum: number, u: any) =>
        sum + (u.responseTimeMs || 0), 0
      );
      const totalMinutes = Math.round(totalTimeMs / 1000 / 60);
      const totalHours = Math.floor(totalMinutes / 60);
      const totalMins = totalMinutes % 60;
      const totalTime = totalHours > 0 ? `${totalHours}h ${totalMins}m` : `${totalMins}m`;

      // Calculate weekly stats
      const weekAgo = new Date();
      weekAgo.setDate(weekAgo.getDate() - 7);

      const weeklyData = usageData.filter((u: any) =>
        new Date(u.date) >= weekAgo
      );

      const weeklySearches = weeklyData.filter((u: any) =>
        u.endpoint?.includes('/api/rag/search')
      ).length;

      const weeklyQuestions = weeklyData.filter((u: any) =>
        u.endpoint?.includes('/api/rag/query')
      ).length;

      const weeklyBookmarkActions = weeklyData.filter((u: any) =>
        u.endpoint?.includes('/api/bookmarks') && u.method === 'POST'
      ).length;

      // Calculate today's stats
      const today = new Date();
      today.setHours(0, 0, 0, 0);

      const todayData = usageData.filter((u: any) => {
        const activityDate = new Date(u.date);
        activityDate.setHours(0, 0, 0, 0);
        return activityDate.getTime() === today.getTime();
      });

      const todaySearches = todayData.filter((u: any) =>
        u.endpoint?.includes('/api/rag/search')
      ).length;

      const todayQuestions = todayData.filter((u: any) =>
        u.endpoint?.includes('/api/rag/query')
      ).length;

      const todayBookmarks = todayData.filter((u: any) =>
        u.endpoint?.includes('/api/bookmarks') && u.method === 'POST'
      ).length;

      const todayTimeMs = todayData.reduce((sum: number, u: any) =>
        sum + (u.responseTimeMs || 0), 0
      );
      const todayMinutes = Math.round(todayTimeMs / 1000 / 60);
      const todayHours = Math.floor(todayMinutes / 60);
      const todayMins = todayMinutes % 60;
      const todayTime = todayHours > 0 ? `${todayHours}h ${todayMins}m` : `${todayMins}m`;

      // Calculate percentage changes
      const prevWeekAgo = new Date();
      prevWeekAgo.setDate(prevWeekAgo.getDate() - 14);

      const prevWeekData = usageData.filter((u: any) => {
        const date = new Date(u.date);
        return date >= prevWeekAgo && date < weekAgo;
      });

      const prevWeekSearches = prevWeekData.filter((u: any) =>
        u.endpoint?.includes('/api/rag/search')
      ).length;

      const prevWeekQuestions = prevWeekData.filter((u: any) =>
        u.endpoint?.includes('/api/rag/query')
      ).length;

      const searchChange = prevWeekSearches > 0
        ? Math.round(((weeklySearches - prevWeekSearches) / prevWeekSearches) * 100)
        : 0;

      const questionChange = prevWeekQuestions > 0
        ? Math.round(((weeklyQuestions - prevWeekQuestions) / prevWeekQuestions) * 100)
        : 0;

      setStats({
        totalSearches: searchCount,
        totalQuestions: questionCount,
        totalBookmarks: bookmarkCount,
        totalTime,
        weeklySearches,
        weeklyQuestions,
        weeklyBookmarks: weeklyBookmarkActions,
        todaySearches,
        todayQuestions,
        todayBookmarks,
        todayTime,
      });

      // Fetch daily usage for chart
      const dailyResponse = await userService.getDailyUsage(30);
      if (dailyResponse) {
        setDailyUsage(dailyResponse);
      }
    } catch (error) {
      console.error('Failed to fetch usage stats:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const maxDailyCount = Math.max(...dailyUsage.map((d: any) => d[1] || 0), 1);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Usage Statistics</h1>
        <p className="mt-2 text-muted-foreground">
          Track your usage of BD Law Assistant
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-100 rounded-lg">
              <Search className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Total Searches</p>
              {isLoading ? (
                <Skeleton className="h-8 w-16 mt-1" />
              ) : (
                <>
                  <p className="text-2xl font-bold">{stats.totalSearches}</p>
                  <p className="text-xs text-muted-foreground mt-1">{stats.weeklySearches} this week</p>
                </>
              )}
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-green-100 rounded-lg">
              <MessageSquare className="h-6 w-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Questions Asked</p>
              {isLoading ? (
                <Skeleton className="h-8 w-16 mt-1" />
              ) : (
                <>
                  <p className="text-2xl font-bold">{stats.totalQuestions}</p>
                  <p className="text-xs text-muted-foreground mt-1">{stats.weeklyQuestions} this week</p>
                </>
              )}
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-yellow-100 rounded-lg">
              <Bookmark className="h-6 w-6 text-yellow-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Bookmarks</p>
              {isLoading ? (
                <Skeleton className="h-8 w-16 mt-1" />
              ) : (
                <>
                  <p className="text-2xl font-bold">{stats.totalBookmarks}</p>
                  <p className="text-xs text-muted-foreground mt-1">{stats.weeklyBookmarks} added this week</p>
                </>
              )}
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-purple-100 rounded-lg">
              <Clock className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Time Spent</p>
              {isLoading ? (
                <Skeleton className="h-8 w-16 mt-1" />
              ) : (
                <>
                  <p className="text-2xl font-bold">{stats.totalTime}</p>
                  <p className="text-xs text-muted-foreground mt-1">All time</p>
                </>
              )}
            </div>
          </div>
        </Card>
      </div>

      {/* Additional Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="p-6">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Daily Activity (Last 30 Days)
          </h2>
          {isLoading ? (
            <Skeleton className="h-64 w-full" />
          ) : dailyUsage.length > 0 ? (
            <div className="space-y-2">
              {dailyUsage.slice(-30).map((day: any, index: number) => (
                <div key={index} className="flex items-center gap-4">
                  <div className="w-20 text-xs text-muted-foreground">
                    {format(new Date(day[0]), 'MMM dd')}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-muted rounded-full h-4 overflow-hidden">
                        <div
                          className="h-full bg-blue-500 rounded-full transition-all"
                          style={{ width: `${(day[1] / maxDailyCount) * 100}%` }}
                        />
                      </div>
                      <div className="w-8 text-xs font-medium text-right">
                        {day[1]}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-muted-foreground border-2 border-dashed rounded-lg">
              <TrendingUp className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No usage data available yet</p>
              <p className="text-xs mt-1">Start using the platform to see your activity</p>
            </div>
          )}
        </Card>

        <Card className="p-6">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Quick Stats
          </h2>
          {isLoading ? (
            <div className="grid grid-cols-2 gap-6">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="text-center">
                  <Skeleton className="h-10 w-16 mx-auto mb-2" />
                  <Skeleton className="h-4 w-24 mx-auto" />
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-6">
              <div className="text-center">
                <p className="text-3xl font-bold text-blue-600">{stats.todaySearches}</p>
                <p className="text-sm text-muted-foreground mt-1">Searches Today</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-green-600">{stats.todayQuestions}</p>
                <p className="text-sm text-muted-foreground mt-1">Questions Today</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-yellow-600">{stats.todayBookmarks}</p>
                <p className="text-sm text-muted-foreground mt-1">Bookmarks Today</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-purple-600">{stats.todayTime}</p>
                <p className="text-sm text-muted-foreground mt-1">Time Today</p>
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
