// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { FormEvent, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import AuthLayout from '../components/AuthLayout';
import { login, extractAuthErrorMessage } from '../lib/authClient';
import { useAuth } from '../lib/authContext';

interface LoginFormState {
  email: string;
  password: string;
}

export function Login() {
  const navigate = useNavigate();
  const { isAuthenticated, setAuth } = useAuth();
  const [form, setForm] = useState<LoginFormState>({ email: '', password: '' });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!form.email || !form.password) {
      setError('Email and password are required');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const result = await login({ email: form.email.trim(), password: form.password });

      if (!result.token) {
        throw new Error('Authentication token missing in response');
      }

      setAuth({ token: result.token, user: result.user, refreshToken: result.refreshToken });
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setError(extractAuthErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthLayout>
      <h2 className="text-center text-2xl font-semibold text-white">Log In</h2>
      <p className="text-center text-sm text-slate-400">
        Access your exponential memory workspace
      </p>

      {error ? (
        <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
          {error}
        </div>
      ) : null}

      <form className="mt-6 space-y-5" onSubmit={handleSubmit} noValidate>
        <div className="space-y-2">
          <label
            htmlFor="login-email"
            className="block text-sm font-semibold uppercase tracking-[0.18em] text-slate-400"
          >
            Email
          </label>
          <input
            type="email"
            placeholder="you@example.com"
            id="login-email"
            value={form.email}
            onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
            className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
            autoComplete="email"
            required
          />
        </div>

        <div className="space-y-2">
          <label
            htmlFor="login-password"
            className="block text-sm font-semibold uppercase tracking-[0.18em] text-slate-400"
          >
            Password
          </label>
          <input
            type="password"
            placeholder="••••••••"
            id="login-password"
            value={form.password}
            onChange={(event) => setForm((prev) => ({ ...prev, password: event.target.value }))}
            className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
            autoComplete="current-password"
            required
          />
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="brand-gradient flex w-full items-center justify-center rounded-xl px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-600/30 transition hover:shadow-indigo-600/45 disabled:cursor-not-allowed disabled:opacity-70"
        >
          {submitting ? 'Signing in...' : 'Log In'}
        </button>
      </form>

      <p className="text-center text-sm text-slate-400">
        Don't have an account?{' '}
        <Link to="/signup" className="font-semibold text-slate-200 transition hover:text-white">
          Sign up
        </Link>
      </p>
    </AuthLayout>
  );
}
