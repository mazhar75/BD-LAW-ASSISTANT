'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Skeleton } from '@/components/ui/Skeleton';
import { useToast } from '@/components/ui/Toast';
import { useAuthStore } from '@/store/authStore';
import { userService } from '@/lib/api/services/user.service';
import {
  User, Mail, Calendar, Shield, Edit, Save, X,
  AlertCircle, CheckCircle, Lock, Globe, Bell
} from 'lucide-react';
import { format } from 'date-fns';
import Link from 'next/link';

const profileSchema = z.object({
  username: z.string().min(3, 'Username must be at least 3 characters'),
  email: z.string().email('Invalid email address'),
  fullName: z.string().min(1, 'Full name is required'),
  phone: z.string().optional(),
  organization: z.string().optional()
});

type ProfileFormData = z.infer<typeof profileSchema>;

export default function ProfilePage() {
  const { showToast } = useToast();
  const user = useAuthStore((state) => state.user);
  const setUser = useAuthStore((state) => state.setUser);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [profile, setProfile] = useState<{
    username: string;
    email: string;
    fullName?: string;
    phoneNumber?: string;
    phone?: string;
    organization?: string;
    createdAt?: string;
    emailVerified?: boolean;
    role?: string;
  } | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset
  } = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema)
  });

  useEffect(() => {
    fetchProfile();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchProfile = async () => {
    try {
      setIsLoading(true);
      const profileData = await userService.getProfile();
      if (profileData) {
        setProfile({
          ...profileData,
          phone: profileData.phoneNumber
        });
        reset({
          username: profileData.username,
          email: profileData.email,
          fullName: profileData.fullName || '',
          phone: profileData.phoneNumber || '',
          organization: ''
        });
      }
    } catch {
      showToast({
        title: 'Error',
        description: 'Failed to load profile',
        type: 'error'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const onSubmit = async (data: ProfileFormData) => {
    try {
      setIsSaving(true);
      const updatedProfile = await userService.updateProfile({
        fullName: data.fullName,
        phoneNumber: data.phone
      });

      if (updatedProfile) {
        setProfile({
          ...updatedProfile,
          phone: updatedProfile.phoneNumber
        });
        setUser({ ...user!, ...updatedProfile });
        setIsEditing(false);
        showToast({
          title: 'Profile Updated',
          description: 'Your profile has been successfully updated',
          type: 'success'
        });
      }
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message :
        (error as { response?: { data?: { message?: string } } })?.response?.data?.message || 'Failed to update profile';
      showToast({
        title: 'Update Failed',
        description: errorMessage,
        type: 'error'
      });
    } finally {
      setIsSaving(false);
    }
  };

  const cancelEdit = () => {
    setIsEditing(false);
    if (profile) {
      reset({
        username: profile.username,
        email: profile.email,
        fullName: profile.fullName || '',
        phone: profile.phone || '',
        organization: ''
      });
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Profile</h1>
          <p className="text-muted-foreground">Manage your account information</p>
        </div>

        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
          </CardHeader>
          <CardContent className="space-y-4">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-3xl font-bold">Profile</h1>
        <p className="text-muted-foreground">Manage your account information</p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Personal Information</CardTitle>
              <CardDescription>Update your personal details</CardDescription>
            </div>
            {!isEditing ? (
              <Button
                onClick={() => setIsEditing(true)}
                variant="outline"
                size="sm"
              >
                <Edit className="h-4 w-4 mr-2" />
                Edit
              </Button>
            ) : (
              <div className="flex gap-2">
                <Button
                  onClick={handleSubmit(onSubmit)}
                  size="sm"
                  loading={isSaving}
                  disabled={isSaving}
                >
                  <Save className="h-4 w-4 mr-2" />
                  Save
                </Button>
                <Button
                  onClick={cancelEdit}
                  variant="ghost"
                  size="sm"
                  disabled={isSaving}
                >
                  <X className="h-4 w-4 mr-2" />
                  Cancel
                </Button>
              </div>
            )}
          </div>
        </CardHeader>

        <CardContent>
          <form className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label htmlFor="username" className="text-sm font-medium">
                  Username
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="username"
                    {...register('username')}
                    className="pl-10"
                    disabled={true}
                  />
                </div>
                <p className="text-xs text-muted-foreground">Username cannot be changed</p>
              </div>

              <div className="space-y-2">
                <label htmlFor="email" className="text-sm font-medium">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="email"
                    type="email"
                    {...register('email')}
                    className="pl-10"
                    disabled={true}
                  />
                </div>
                <p className="text-xs text-muted-foreground">Contact support to change email</p>
              </div>
            </div>

            <div className="space-y-2">
              <label htmlFor="fullName" className="text-sm font-medium">
                Full Name
              </label>
              <Input
                id="fullName"
                {...register('fullName')}
                placeholder="John Doe"
                disabled={!isEditing || isSaving}
              />
              {errors.fullName && (
                <p className="text-sm text-destructive flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" />
                  {errors.fullName.message}
                </p>
              )}
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label htmlFor="phone" className="text-sm font-medium">
                  Phone Number
                </label>
                <Input
                  id="phone"
                  {...register('phone')}
                  placeholder="+880 1234567890"
                  disabled={!isEditing || isSaving}
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="organization" className="text-sm font-medium">
                  Organization
                </label>
                <Input
                  id="organization"
                  {...register('organization')}
                  placeholder="Law Firm / Company"
                  disabled={!isEditing || isSaving}
                />
              </div>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Account Information</CardTitle>
          <CardDescription>View your account status and settings</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between py-2">
            <div className="flex items-center gap-3">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Member Since</p>
                <p className="text-xs text-muted-foreground">
                  {profile?.createdAt ? format(new Date(profile.createdAt), 'MMMM dd, yyyy') : 'N/A'}
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between py-2">
            <div className="flex items-center gap-3">
              <Shield className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Account Status</p>
                <p className="text-xs text-muted-foreground flex items-center gap-1">
                  {profile?.emailVerified ? (
                    <>
                      <CheckCircle className="h-3 w-3 text-green-600" />
                      Verified
                    </>
                  ) : (
                    <>
                      <AlertCircle className="h-3 w-3 text-yellow-600" />
                      Unverified
                    </>
                  )}
                </p>
              </div>
            </div>
            {!profile?.emailVerified && (
              <Button size="sm" variant="outline">
                Verify Email
              </Button>
            )}
          </div>

          <div className="flex items-center justify-between py-2">
            <div className="flex items-center gap-3">
              <Globe className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Account Type</p>
                <p className="text-xs text-muted-foreground">
                  {profile?.role === 'ADMIN' ? 'Administrator' : 'Standard User'}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Common account tasks</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-2">
            <Link href="/settings/password">
              <Button variant="outline" className="w-full justify-start">
                <Lock className="h-4 w-4 mr-2" />
                Change Password
              </Button>
            </Link>
            <Link href="/settings/preferences">
              <Button variant="outline" className="w-full justify-start">
                <Bell className="h-4 w-4 mr-2" />
                Notification Settings
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}