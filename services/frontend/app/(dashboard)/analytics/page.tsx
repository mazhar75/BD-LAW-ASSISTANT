'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { userService } from '@/lib/api/services/user.service';
import { BarChart3, TrendingUp, Clock, Search, MessageSquare, Eye } from 'lucide-react';
import { format } from 'date-fns';

interface UsageStats {
  totalRequests: number;
  averageResponseTime: number;
  topEndpoints: Array<[string, number]>;
}

interface DailyUsage {
  date: string;
  count: number;
}

export default function AnalyticsPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [stats, setStats] = useState<UsageStats | null>(null);
  const [dailyUsage, setDailyUsage] = useState<DailyUsage[]>([]);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      setIsLoading(true);

      // Fetch usage statistics
      const usageResponse = await userService.getUsage();
      if (usageResponse && usageResponse.summary) {
        setStats(usageResponse.summary);
      }

      // Fetch daily usage
      const dailyResponse = await userService.getDailyUsage(30);
      if (dailyResponse) {
        const formattedData = dailyResponse.map((item: any[]) => ({
          date: item[0],
          count: item[1]
        }));
        setDailyUsage(formattedData);
      }
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const maxDailyCount = Math.max(...dailyUsage.map(d => d.count), 1);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
        <p className="text-muted-foreground">
          Detailed insights into your usage patterns
        </p>
      </div>

      {/* Summary Statistics */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Requests</CardTitle>
            <Search className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <div className="text-2xl font-bold">{stats?.totalRequests || 0}</div>
            )}
            <p className="text-xs text-muted-foreground mt-1">All-time requests</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <div className="text-2xl font-bold">
                {stats?.averageResponseTime ? `${stats.averageResponseTime.toFixed(0)}ms` : '0ms'}
              </div>
            )}
            <p className="text-xs text-muted-foreground mt-1">Average response time</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Activity Trend</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <div className="text-2xl font-bold text-green-600">
                {dailyUsage.length > 0 ? '+' : ''}
                {dailyUsage.slice(-7).reduce((sum, d) => sum + d.count, 0)}
              </div>
            )}
            <p className="text-xs text-muted-foreground mt-1">Last 7 days</p>
          </CardContent>
        </Card>
      </div>

      {/* Daily Usage Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Daily Usage (Last 30 Days)</CardTitle>
          <CardDescription>Your activity over the past month</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-64 w-full" />
          ) : dailyUsage.length > 0 ? (
            <div className="space-y-3">
              {dailyUsage.slice(-30).map((day, index) => (
                <div key={index} className="flex items-center gap-4">
                  <div className="w-24 text-sm text-muted-foreground">
                    {format(new Date(day.date), 'MMM dd')}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-muted rounded-full h-6 overflow-hidden">
                        <div
                          className="h-full bg-blue-500 rounded-full transition-all"
                          style={{ width: `${(day.count / maxDailyCount) * 100}%` }}
                        />
                      </div>
                      <div className="w-12 text-sm font-medium text-right">
                        {day.count}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <BarChart3 className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>No usage data available yet</p>
              <p className="text-sm mt-1">Start using the platform to see your activity here</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Top Endpoints */}
      <Card>
        <CardHeader>
          <CardTitle>Most Used Features</CardTitle>
          <CardDescription>Your frequently accessed endpoints</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : stats?.topEndpoints && stats.topEndpoints.length > 0 ? (
            <div className="space-y-3">
              {stats.topEndpoints.slice(0, 5).map(([endpoint, count], index) => (
                <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                      <span className="text-sm font-bold text-primary">{index + 1}</span>
                    </div>
                    <div>
                      <p className="font-medium text-sm">{endpoint}</p>
                      <p className="text-xs text-muted-foreground">{count} requests</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-semibold">{count}</div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <Eye className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>No feature usage data yet</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
