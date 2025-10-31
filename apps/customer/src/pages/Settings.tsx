// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// Authenticated settings page for profile, security, and preferences.

import { FormEvent, useEffect, useMemo, useState } from 'react';
import type { AxiosError } from 'axios';
import { Navigation } from '../components/Navigation';
import apiClient from '../lib/apiClient';
import { useAuth } from '../lib/authContext';

interface UserProfileResponse {
  id: string;
  email: string | null;
  name: string;
  account_type: string;
  subscription_tier: string;
  role: string;
  email_verified: boolean;
  is_active: boolean;
  created_at: string;
  last_login: string | null;
}

type ThemePreference = 'light' | 'dark' | 'auto';

interface PreferencesResponse {
  email_notifications: boolean;
  theme: ThemePreference;
  updated_at?: string | null;
}

interface PasswordFormState {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

const SAMPLE_PROFILE: UserProfileResponse = {
  id: 'demo-user-001',
  email: 'kanna@ninaivalaigal.ai',
  name: 'Kalaivani "Kanna" Subramani',
  account_type: 'enterprise',
  subscription_tier: 'founders',
  role: 'memory lead',
  email_verified: true,
  is_active: true,
  created_at: new Date(Date.now() - 86400 * 180 * 1000).toISOString(),
  last_login: new Date().toISOString(),
};

const SAMPLE_PREFERENCES: PreferencesResponse = {
  email_notifications: true,
  theme: 'auto',
  updated_at: new Date().toISOString(),
};

export default function Settings() {
  const { user, updateUser } = useAuth();
  const [profile, setProfile] = useState<UserProfileResponse | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [usingFallback, setUsingFallback] = useState(false);

  const [preferences, setPreferences] = useState<PreferencesResponse>({
    email_notifications: true,
    theme: 'auto',
  });
  const [preferencesStatus, setPreferencesStatus] = useState<string | null>(null);
  const [preferencesError, setPreferencesError] = useState<string | null>(null);
  const [savingPreferences, setSavingPreferences] = useState(false);

  const [passwordForm, setPasswordForm] = useState<PasswordFormState>({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [passwordStatus, setPasswordStatus] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [changingPassword, setChangingPassword] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const controller = new AbortController();

    async function loadSettings() {
      try {
        setLoadingProfile(true);
        const [profileRes, preferencesRes] = await Promise.all([
          apiClient.get<UserProfileResponse>('/users/me', { signal: controller.signal }),
          apiClient.get<PreferencesResponse>('/users/me/preferences', { signal: controller.signal }),
        ]);

        if (!isMounted) {
          return;
        }

        setProfile(profileRes.data);
        setPreferences({
          email_notifications: preferencesRes.data.email_notifications,
          theme: preferencesRes.data.theme,
          updated_at: preferencesRes.data.updated_at,
        });

        updateUser({
          id: profileRes.data.id,
          email: profileRes.data.email ?? user?.email ?? '',
          name: profileRes.data.name,
          accountType: profileRes.data.account_type,
          role: profileRes.data.role,
        });
        setProfileError(null);
        setUsingFallback(false);
      } catch (error) {
        if (!isMounted) {
          return;
        }

        const axiosError = error as AxiosError<{ detail?: string }>;
        const message = axiosError.response?.data?.detail || axiosError.message || 'Unable to load settings';
        setProfileError(message);
  setProfile({ ...SAMPLE_PROFILE });
  setPreferences({ ...SAMPLE_PREFERENCES });
        updateUser({
          id: SAMPLE_PROFILE.id,
          email: SAMPLE_PROFILE.email ?? user?.email ?? '',
          name: SAMPLE_PROFILE.name,
          accountType: SAMPLE_PROFILE.account_type,
          role: SAMPLE_PROFILE.role,
        });
        setUsingFallback(true);
      } finally {
        if (isMounted) {
          setLoadingProfile(false);
        }
      }
    }

    loadSettings();

    return () => {
      isMounted = false;
      controller.abort();
    };
  }, [updateUser, user?.email]);

  const memberSince = useMemo(() => {
    if (!profile?.created_at) {
      return null;
    }
    const created = new Date(profile.created_at);
    return new Intl.DateTimeFormat(undefined, {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    }).format(created);
  }, [profile]);

  const handlePasswordSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setPasswordStatus(null);
    setPasswordError(null);

    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      setPasswordError('New passwords do not match');
      return;
    }

    setChangingPassword(true);
    try {
  await apiClient.post('/users/me/password', {
        current_password: passwordForm.currentPassword,
        new_password: passwordForm.newPassword,
        confirm_password: passwordForm.confirmPassword,
      });
      setPasswordStatus('Password updated successfully');
      setPasswordForm({ currentPassword: '', newPassword: '', confirmPassword: '' });
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: string }>;
      const message = axiosError.response?.data?.detail || axiosError.message || 'Unable to update password';
      setPasswordError(message);
    } finally {
      setChangingPassword(false);
    }
  };

  const handlePreferencesSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setPreferencesStatus(null);
    setPreferencesError(null);
    setSavingPreferences(true);

    try {
  const response = await apiClient.put<PreferencesResponse>('/users/me/preferences', {
        email_notifications: preferences.email_notifications,
        theme: preferences.theme,
      });
      setPreferences((prev) => ({ ...prev, updated_at: response.data.updated_at }));
      setPreferencesStatus('Preferences saved');
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: string }>;
      const message = axiosError.response?.data?.detail || axiosError.message || 'Unable to save preferences';
      setPreferencesError(message);
    } finally {
      setSavingPreferences(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-100">
      <Navigation variant="dark" className="sticky top-0 z-20" />
      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
        <header className="space-y-2">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            Settings
          </h1>
          <p className="text-slate-400 max-w-2xl">
            Manage your profile, security, and workspace preferences.
          </p>
        </header>

        {usingFallback ? (
          <div className="rounded-3xl border border-amber-400/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
            API connection failed ({profileError}). Displaying sample profile and workspace preferences so the experience stays navigable while services are offline.
          </div>
        ) : null}

        <section className="rounded-3xl border border-white/5 bg-white/5 backdrop-blur-xl shadow-2xl p-6 sm:p-8">
          <h2 className="text-xl font-semibold text-white mb-4">Profile Overview</h2>
          {loadingProfile ? (
            <div className="flex items-center space-x-3 text-slate-400">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-400 border-t-transparent"></div>
              <span>Loading profile…</span>
            </div>
          ) : profile ? (
            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-6 text-sm">
              <div>
                <dt className="text-slate-400 uppercase tracking-[0.18em] text-xs mb-1">Name</dt>
                <dd className="text-white text-base font-medium">{profile.name}</dd>
              </div>
              <div>
                <dt className="text-slate-400 uppercase tracking-[0.18em] text-xs mb-1">Email</dt>
                <dd className="text-white text-base font-medium">{profile.email ?? user?.email ?? '—'}</dd>
              </div>
              <div>
                <dt className="text-slate-400 uppercase tracking-[0.18em] text-xs mb-1">Account Type</dt>
                <dd className="text-white text-base font-medium capitalize">{profile.account_type}</dd>
              </div>
              <div>
                <dt className="text-slate-400 uppercase tracking-[0.18em] text-xs mb-1">Subscription</dt>
                <dd className="text-white text-base font-medium capitalize">{profile.subscription_tier}</dd>
              </div>
              <div>
                <dt className="text-slate-400 uppercase tracking-[0.18em] text-xs mb-1">Member Since</dt>
                <dd className="text-white text-base font-medium">{memberSince ?? '—'}</dd>
              </div>
              <div>
                <dt className="text-slate-400 uppercase tracking-[0.18em] text-xs mb-1">Status</dt>
                <dd className="text-white text-base font-medium">{profile.email_verified ? 'Email verified' : 'Pending verification'}</dd>
              </div>
            </dl>
          ) : (
            <p className="text-rose-300">{profileError ?? 'Unable to load profile'}</p>
          )}
        </section>

        <section className="rounded-3xl border border-white/5 bg-white/5 backdrop-blur-xl shadow-2xl p-6 sm:p-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
            <h2 className="text-xl font-semibold text-white">Change Password</h2>
            {passwordStatus ? <span className="text-emerald-300 text-sm font-medium">{passwordStatus}</span> : null}
          </div>
          {passwordError ? (
            <div className="mb-4 rounded-2xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
              {passwordError}
            </div>
          ) : null}
          <form className="grid gap-5" onSubmit={handlePasswordSubmit} noValidate>
            <label className="grid gap-2">
              <span className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Current Password</span>
              <input
                type="password"
                value={passwordForm.currentPassword}
                onChange={(event) =>
                  setPasswordForm((prev) => ({ ...prev, currentPassword: event.target.value }))
                }
                className="rounded-xl border border-white/10 bg-slate-900/70 px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
                autoComplete="current-password"
                required
              />
            </label>
            <label className="grid gap-2">
              <span className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">New Password</span>
              <input
                type="password"
                value={passwordForm.newPassword}
                onChange={(event) =>
                  setPasswordForm((prev) => ({ ...prev, newPassword: event.target.value }))
                }
                className="rounded-xl border border-white/10 bg-slate-900/70 px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
                autoComplete="new-password"
                required
              />
            </label>
            <label className="grid gap-2">
              <span className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Confirm Password</span>
              <input
                type="password"
                value={passwordForm.confirmPassword}
                onChange={(event) =>
                  setPasswordForm((prev) => ({ ...prev, confirmPassword: event.target.value }))
                }
                className="rounded-xl border border-white/10 bg-slate-900/70 px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
                autoComplete="new-password"
                required
              />
            </label>
            <button
              type="submit"
              disabled={changingPassword}
              className="brand-gradient flex w-full sm:w-auto items-center justify-center rounded-xl px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-600/30 transition hover:shadow-indigo-600/45 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {changingPassword ? 'Updating…' : 'Update Password'}
            </button>
          </form>
        </section>

        <section className="rounded-3xl border border-white/5 bg-white/5 backdrop-blur-xl shadow-2xl p-6 sm:p-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
            <h2 className="text-xl font-semibold text-white">Preferences</h2>
            {preferences?.updated_at ? (
              <span className="text-xs uppercase tracking-[0.2em] text-slate-400">
                Updated {new Date(preferences.updated_at).toLocaleString()}
              </span>
            ) : null}
          </div>
          {preferencesStatus ? (
            <div className="mb-4 rounded-2xl border border-emerald-500/40 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
              {preferencesStatus}
            </div>
          ) : null}
          {preferencesError ? (
            <div className="mb-4 rounded-2xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
              {preferencesError}
            </div>
          ) : null}
          <form className="grid gap-6" onSubmit={handlePreferencesSubmit}>
            <label className="flex items-center justify-between gap-4">
              <span className="text-sm text-slate-200">Email notifications</span>
              <div className="relative inline-flex items-center">
                <input
                  type="checkbox"
                  checked={preferences.email_notifications}
                  onChange={(event) =>
                    setPreferences((prev) => ({ ...prev, email_notifications: event.target.checked }))
                  }
                  className="peer sr-only"
                />
                <div className="h-6 w-10 rounded-full bg-slate-600 transition peer-checked:bg-indigo-500">
                  <div className="absolute top-1 left-1 h-4 w-4 rounded-full bg-white transition peer-checked:translate-x-4"></div>
                </div>
              </div>
            </label>

            <label className="grid gap-2">
              <span className="text-sm text-slate-200">Theme</span>
              <select
                value={preferences.theme}
                onChange={(event) =>
                  setPreferences((prev) => ({ ...prev, theme: event.target.value as ThemePreference }))
                }
                className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-3 text-sm text-slate-100 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
              >
                <option value="auto">Auto</option>
                <option value="light">Light</option>
                <option value="dark">Dark</option>
              </select>
            </label>

            <button
              type="submit"
              disabled={savingPreferences}
              className="brand-gradient flex w-full sm:w-auto items-center justify-center rounded-xl px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-600/30 transition hover:shadow-indigo-600/45 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {savingPreferences ? 'Saving…' : 'Save Preferences'}
            </button>
          </form>
        </section>

        {/* JWT Token & API Access Section */}
        <section className="rounded-3xl border border-white/5 bg-white/5 backdrop-blur-xl shadow-2xl p-6 sm:p-8">
          <div className="flex flex-col gap-2 mb-6">
            <h2 className="text-xl font-semibold text-white">API Access & Authentication</h2>
            <p className="text-sm text-slate-400">Your JWT token for API access and development</p>
          </div>

          {(() => {
            const token = localStorage.getItem('nina.auth.token');
            if (!token) {
              return (
                <div className="rounded-2xl border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
                  No authentication token found. Please log in again.
                </div>
              );
            }

            // Decode JWT to get expiration
            interface JWTPayload {
              exp?: number;
              user_id?: string;
              account_type?: string;
            }
            let decodedPayload: JWTPayload | null = null;
            let expiresAt: Date | null = null;
            let isExpired = false;
            let timeRemaining = '';

            try {
              const payloadBase64 = token.split('.')[1];
              const payloadJson = atob(payloadBase64);
              decodedPayload = JSON.parse(payloadJson);

              if (decodedPayload?.exp) {
                expiresAt = new Date(decodedPayload.exp * 1000);
                isExpired = expiresAt < new Date();

                const msRemaining = expiresAt.getTime() - Date.now();
                if (msRemaining > 0) {
                  const days = Math.floor(msRemaining / (1000 * 60 * 60 * 24));
                  const hours = Math.floor((msRemaining % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                  timeRemaining = days > 0 ? `${days}d ${hours}h remaining` : `${hours}h remaining`;
                }
              }
            } catch (e) {
              console.error('Failed to decode JWT:', e);
            }

            const copyToken = () => {
              navigator.clipboard.writeText(token);
              alert('Token copied to clipboard!');
            };

            return (
              <div className="space-y-6">
                {/* Token Status */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                  <div>
                    <dt className="text-slate-400 uppercase tracking-[0.18em] text-xs mb-1">Status</dt>
                    <dd className={`text-base font-medium ${isExpired ? 'text-rose-400' : 'text-emerald-400'}`}>
                      {isExpired ? '❌ Expired' : '✅ Valid'}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-slate-400 uppercase tracking-[0.18em] text-xs mb-1">Expires</dt>
                    <dd className="text-white text-base font-medium">
                      {expiresAt ? expiresAt.toLocaleString() : 'Unknown'}
                      {timeRemaining && <span className="text-xs text-slate-400 ml-2">({timeRemaining})</span>}
                    </dd>
                  </div>
                  {decodedPayload?.user_id && (
                    <div>
                      <dt className="text-slate-400 uppercase tracking-[0.18em] text-xs mb-1">User ID</dt>
                      <dd className="text-white text-base font-mono text-xs">{decodedPayload.user_id}</dd>
                    </div>
                  )}
                  {decodedPayload?.account_type && (
                    <div>
                      <dt className="text-slate-400 uppercase tracking-[0.18em] text-xs mb-1">Account Type</dt>
                      <dd className="text-white text-base font-medium capitalize">{decodedPayload.account_type}</dd>
                    </div>
                  )}
                </div>

                {/* JWT Token Display */}
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-[0.18em] text-slate-400 mb-2">
                    JWT Token
                  </label>
                  <div className="relative">
                    <textarea
                      readOnly
                      value={token}
                      className="w-full h-32 rounded-xl border border-white/10 bg-slate-900/70 px-4 py-3 text-xs font-mono text-slate-300 resize-none focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
                    />
                    <button
                      type="button"
                      onClick={copyToken}
                      className="absolute top-2 right-2 bg-indigo-600 hover:bg-indigo-500 text-white px-3 py-1.5 rounded-lg text-xs font-medium transition"
                    >
                      📋 Copy
                    </button>
                  </div>
                  <p className="mt-2 text-xs text-slate-400">
                    Use this token in the <code className="text-indigo-400">Authorization: Bearer &lt;token&gt;</code> header for API requests.
                  </p>
                </div>

                {/* Usage Example */}
                <details className="group">
                  <summary className="cursor-pointer text-sm font-medium text-indigo-400 hover:text-indigo-300 transition">
                    Show API usage example
                  </summary>
                  <div className="mt-3 rounded-xl border border-white/10 bg-slate-900/70 p-4">
                    <pre className="text-xs text-slate-300 overflow-x-auto">
{`curl -X GET http://localhost:13390/users/me \\
  -H "Authorization: Bearer ${token.substring(0, 20)}..." \\
  -H "Content-Type: application/json"`}
                    </pre>
                  </div>
                </details>
              </div>
            );
          })()}
        </section>
      </main>
    </div>
  );
}
