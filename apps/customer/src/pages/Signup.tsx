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
import { signupIndividual, signupOrganization, extractAuthErrorMessage } from '../lib/authClient';
import { useAuth } from '../lib/authContext';

type AccountType = 'individual' | 'organization';

interface SignupFormState {
  accountType: AccountType;
  name: string;
  email: string;
  password: string;
  organizationName: string;
  organizationDomain: string;
  organizationSize: string;
  organizationIndustry: string;
}

const initialFormState: SignupFormState = {
  accountType: 'individual',
  name: '',
  email: '',
  password: '',
  organizationName: '',
  organizationDomain: '',
  organizationSize: '',
  organizationIndustry: '',
};

export function Signup() {
  const navigate = useNavigate();
  const { isAuthenticated, setAuth } = useAuth();
  const [form, setForm] = useState<SignupFormState>(initialFormState);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    // Validate common fields
    if (!form.name || !form.email || !form.password) {
      setError('Name, email, and password are required');
      return;
    }

    // Validate organization fields
    if (form.accountType === 'organization' && !form.organizationName) {
      setError('Organization name is required');
      return;
    }

    setSubmitting(true);
    setError(null);
    setSuccessMessage(null);

    try {
      let result;

      if (form.accountType === 'organization') {
        result = await signupOrganization({
          email: form.email.trim(),
          password: form.password,
          fullName: form.name.trim(),
          organizationName: form.organizationName.trim(),
          organizationDomain: form.organizationDomain.trim() || undefined,
          organizationSize: form.organizationSize || undefined,
          organizationIndustry: form.organizationIndustry.trim() || undefined,
        });
      } else {
        result = await signupIndividual({
          name: form.name.trim(),
          fullName: form.name.trim(),
          email: form.email.trim(),
          password: form.password,
          accountType: 'individual',
        });
      }

      if (result.token) {
        setAuth({ token: result.token, user: result.user, refreshToken: result.refreshToken });
        navigate('/dashboard', { replace: true });
        return;
      }

      const message =
        result.message ||
        'Signup successful. Please check your email to verify your account before logging in.';
      setSuccessMessage(message);
      setForm(initialFormState);
    } catch (err) {
      setError(extractAuthErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthLayout>
      <h2 className="text-center text-2xl font-semibold text-white">Create your workspace</h2>
      <p className="text-center text-sm text-slate-400">
        Unlock guided memory capture and institutional intelligence
      </p>

      {error ? (
        <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
          {error}
        </div>
      ) : null}

      {successMessage ? (
        <div className="rounded-xl border border-emerald-500/40 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
          {successMessage}
        </div>
      ) : null}

      <form className="mt-6 space-y-5" onSubmit={handleSubmit} noValidate>
        {/* Account Type Selector */}
        <div className="space-y-2">
          <label className="block text-sm font-semibold uppercase tracking-[0.18em] text-slate-400">
            Account Type
          </label>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => setForm((prev) => ({ ...prev, accountType: 'individual' }))}
              className={`flex-1 rounded-xl px-4 py-3 text-sm font-medium transition ${
                form.accountType === 'individual'
                  ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/30'
                  : 'bg-slate-800/50 text-slate-300 hover:bg-slate-800'
              }`}
            >
              👤 Individual
            </button>
            <button
              type="button"
              onClick={() => setForm((prev) => ({ ...prev, accountType: 'organization' }))}
              className={`flex-1 rounded-xl px-4 py-3 text-sm font-medium transition ${
                form.accountType === 'organization'
                  ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/30'
                  : 'bg-slate-800/50 text-slate-300 hover:bg-slate-800'
              }`}
            >
              🏢 Organization
            </button>
          </div>
        </div>

        {/* Common Fields */}
        <div className="space-y-2">
          <label htmlFor="signup-name" className="block text-sm font-semibold uppercase tracking-[0.18em] text-slate-400">
            Your Name
          </label>
          <input
            type="text"
            placeholder="Jane Doe"
            id="signup-name"
            value={form.name}
            onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
            className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
            autoComplete="name"
            required
          />
        </div>

        <div className="space-y-2">
          <label htmlFor="signup-email" className="block text-sm font-semibold uppercase tracking-[0.18em] text-slate-400">
            Email
          </label>
          <input
            type="email"
            placeholder="you@example.com"
            id="signup-email"
            value={form.email}
            onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
            className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
            autoComplete="email"
            required
          />
        </div>

        <div className="space-y-2">
          <label htmlFor="signup-password" className="block text-sm font-semibold uppercase tracking-[0.18em] text-slate-400">
            Password
          </label>
          <input
            type="password"
            placeholder="••••••••"
            id="signup-password"
            value={form.password}
            onChange={(event) => setForm((prev) => ({ ...prev, password: event.target.value }))}
            className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
            autoComplete="new-password"
            required
          />
        </div>

        {/* Organization Fields - Only show if organization is selected */}
        {form.accountType === 'organization' && (
          <>
            <div className="space-y-2">
              <label htmlFor="org-name" className="block text-sm font-semibold uppercase tracking-[0.18em] text-slate-400">
                Organization Name *
              </label>
              <input
                type="text"
                placeholder="Acme Corporation"
                id="org-name"
                value={form.organizationName}
                onChange={(event) => setForm((prev) => ({ ...prev, organizationName: event.target.value }))}
                className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
                required
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="org-domain" className="block text-sm font-semibold uppercase tracking-[0.18em] text-slate-400">
                Organization Domain
              </label>
              <input
                type="text"
                placeholder="acmecorp.com"
                id="org-domain"
                value={form.organizationDomain}
                onChange={(event) => setForm((prev) => ({ ...prev, organizationDomain: event.target.value }))}
                className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <label htmlFor="org-size" className="block text-sm font-semibold uppercase tracking-[0.18em] text-slate-400">
                  Company Size
                </label>
                <select
                  id="org-size"
                  value={form.organizationSize}
                  onChange={(event) => setForm((prev) => ({ ...prev, organizationSize: event.target.value }))}
                  className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-3 text-sm text-slate-100 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
                >
                  <option value="">Select size</option>
                  <option value="1-10">1-10</option>
                  <option value="11-50">11-50</option>
                  <option value="51-200">51-200</option>
                  <option value="201-500">201-500</option>
                  <option value="501+">501+</option>
                </select>
              </div>

              <div className="space-y-2">
                <label htmlFor="org-industry" className="block text-sm font-semibold uppercase tracking-[0.18em] text-slate-400">
                  Industry
                </label>
                <select
                  id="org-industry"
                  value={form.organizationIndustry}
                  onChange={(event) => setForm((prev) => ({ ...prev, organizationIndustry: event.target.value }))}
                  className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-3 text-sm text-slate-100 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
                >
                  <option value="">Select industry</option>
                  <option value="Technology">Technology</option>
                  <option value="Healthcare">Healthcare</option>
                  <option value="Finance">Finance</option>
                  <option value="Education">Education</option>
                  <option value="Retail">Retail</option>
                  <option value="Manufacturing">Manufacturing</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>
          </>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="brand-gradient flex w-full items-center justify-center rounded-xl px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-600/30 transition hover:shadow-indigo-600/45 disabled:cursor-not-allowed disabled:opacity-70"
        >
          {submitting ? 'Creating account...' : `Sign Up as ${form.accountType === 'organization' ? 'Organization' : 'Individual'}`}
        </button>
      </form>

      <p className="text-center text-sm text-slate-400">
        Already have an account?{' '}
        <Link to="/login" className="font-semibold text-slate-200 transition hover:text-white">
          Log in
        </Link>
      </p>
    </AuthLayout>
  );
}
