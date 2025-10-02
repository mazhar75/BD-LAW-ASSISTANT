'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { useAuthStore } from '@/store/authStore';
import { userService } from '@/lib/api/services/user.service';
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
      const response = await userService.getUsage();
      setUsage(response);
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
      title: 'Total Searches',
      value: usage?.totalSearches || 0,
      icon: Search,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
      change: '+12%',
      trend: 'up'
    },
    {
      title: 'Questions Asked',
      value: usage?.totalQuestions || 0,
      icon: MessageSquare,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
      change: '+8%',
      trend: 'up'
    },
    {
      title: 'Laws Viewed',
      value: usage?.lawsViewed || 0,
      icon: BookOpen,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
      change: '+15%',
      trend: 'up'
    },
    {
      title: 'Saved Items',
      value: usage?.savedItems || 0,
      icon: FileText,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
      change: '+5%',
      trend: 'up'
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
                  <div className="flex items-center text-xs text-muted-foreground">
                    {stat.trend === 'up' ? (
                      <TrendingUp className="h-3 w-3 text-green-500 mr-1" />
                    ) : (
                      <TrendingUp className="h-3 w-3 text-red-500 mr-1 rotate-180" />
                    )}
                    <span className={stat.trend === 'up' ? 'text-green-500' : 'text-red-500'}>
                      {stat.change}
                    </span>
                    <span className="ml-1">from last month</span>
                  </div>
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