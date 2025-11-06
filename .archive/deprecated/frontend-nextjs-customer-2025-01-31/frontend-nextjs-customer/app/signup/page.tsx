// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useMemo, useState } from 'react';
import { Badge, Button, Card, Input } from '@ninaivalaigal/ui-components';
import { useAuth } from '../../contexts/AuthContext';
import type { SignupRequest } from '../../types/api';

type SignupFormState = {
  email: string;
  username: string;
  password: string;
  confirmPassword: string;
};

type SignupErrors = Partial<Record<keyof SignupFormState, string>>;

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const passwordRequirements = [
  { id: 'length', label: '8+ characters', test: (value: string) => value.length >= 8 },
  { id: 'uppercase', label: 'Uppercase letter', test: (value: string) => /[A-Z]/.test(value) },
  { id: 'lowercase', label: 'Lowercase letter', test: (value: string) => /[a-z]/.test(value) },
  { id: 'number', label: 'Number', test: (value: string) => /\d/.test(value) },
] as const;

const initialFormState: SignupFormState = {
  email: '',
  username: '',
  password: '',
  confirmPassword: '',
};

export default function SignupPage() {
  const router = useRouter();
  const { signup, isLoading } = useAuth();

  const [formState, setFormState] = useState<SignupFormState>(initialFormState);
  const [fieldErrors, setFieldErrors] = useState<SignupErrors>({});
  const [submitError, setSubmitError] = useState<string | null>(null);

  const passwordStrength = useMemo(() => {
    const satisfied = passwordRequirements.filter((check) => check.test(formState.password)).length;

    if (!formState.password) {
      return { label: 'Add a password', variant: 'neutral' as const };
    }

    if (satisfied <= 1) {
      return { label: 'Weak', variant: 'danger' as const };
    }

    if (satisfied === 2) {
      return { label: 'Fair', variant: 'warning' as const };
    }

    if (satisfied === 3) {
      return { label: 'Good', variant: 'info' as const };
    }

    return { label: 'Strong', variant: 'success' as const };
  }, [formState.password]);

  const validateForm = (): SignupErrors => {
    const errors: SignupErrors = {};
    const email = formState.email.trim();
    const username = formState.username.trim();
    const password = formState.password;
    const confirmPassword = formState.confirmPassword;

    if (!email) {
      errors.email = 'Email is required';
    } else if (!EMAIL_REGEX.test(email)) {
      errors.email = 'Enter a valid email address';
    }

    if (username && username.length < 3) {
      errors.username = 'Username must be at least 3 characters';
    } else if (username && !/^[a-zA-Z0-9_-]+$/.test(username)) {
      errors.username = 'Use only letters, numbers, hyphen, or underscore';
    }

    if (!password) {
      errors.password = 'Password is required';  // pragma: allowlist secret
    } else if (password.length < 8) {
      errors.password = 'Password must be at least 8 characters';  // pragma: allowlist secret
    } else if (!/[A-Z]/.test(password) || !/[a-z]/.test(password) || !/\d/.test(password)) {
      errors.password = 'Password must include uppercase, lowercase, and a number';  // pragma: allowlist secret
    }

    if (!confirmPassword) {
      errors.confirmPassword = 'Confirm your password';  // pragma: allowlist secret
    } else if (password !== confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';  // pragma: allowlist secret
    }

    setFieldErrors(errors);
    return errors;
  };

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    const fieldName = name as keyof SignupFormState;

    setFormState((prev) => ({
      ...prev,
      [fieldName]: value,
    }));

    if (fieldErrors[fieldName]) {
      setFieldErrors((prev) => {
        const next = { ...prev };
        delete next[fieldName];
        return next;
      });
    }

    if (submitError) {
      setSubmitError(null);
    }
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitError(null);

    const errors = validateForm();
    if (Object.keys(errors).length > 0) {
      return;
    }

    const email = formState.email.trim().toLowerCase();
  const username = formState.username.trim();

    const payload: SignupRequest = {
      email,
      password: formState.password,
      ...(username ? { username } : {}),
    };

    const result = await signup(payload);

    if (result.error) {
      setSubmitError(result.error);
      return;
    }

    setFormState(initialFormState);
    setFieldErrors({});
    router.push('/dashboard');
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12">
      <Card className="w-full max-w-xl bg-white p-8 text-gray-900 shadow-xl">
        <div className="space-y-8">
          <div className="space-y-2 text-center">
            <h1 className="text-3xl font-bold tracking-tight text-gray-900">
              Create your Ninaivalaigal account
            </h1>
            <p className="text-sm text-gray-600">
              Start capturing, organizing, and sharing memories in minutes.
            </p>
          </div>

          {submitError && (
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-800">
              {submitError}
            </div>
          )}

          <form className="space-y-6" onSubmit={handleSubmit} noValidate>
            <div className="space-y-1">
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email address
              </label>
              <Input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={formState.email}
                onChange={handleChange}
                className="mt-1"
                isInvalid={Boolean(fieldErrors.email)}
                placeholder="you@example.com"
                disabled={isLoading}
                variant="default"
              />
              {fieldErrors.email && (
                <p className="text-sm text-red-600">{fieldErrors.email}</p>
              )}
            </div>

            <div className="space-y-1">
              <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                Display name <span className="text-gray-400">(optional)</span>
              </label>
              <Input
                id="username"
                name="username"
                type="text"
                autoComplete="name"
                value={formState.username}
                onChange={handleChange}
                className="mt-1"
                isInvalid={Boolean(fieldErrors.username)}
                placeholder="For example: Priya from Ninaivalaigal"
                disabled={isLoading}
                variant="default"
              />
              {fieldErrors.username && (
                <p className="text-sm text-red-600">{fieldErrors.username}</p>
              )}
            </div>

            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                  Password
                </label>
                {formState.password && (
                  <Badge variant={passwordStrength.variant} pill>
                    {passwordStrength.label}
                  </Badge>
                )}
              </div>
              <Input
                id="password"
                name="password"
                type="password"
                autoComplete="new-password"
                required
                value={formState.password}
                onChange={handleChange}
                className="mt-1"
                isInvalid={Boolean(fieldErrors.password)}
                placeholder="••••••••"
                disabled={isLoading}
                variant="default"
              />
              {fieldErrors.password && (
                <p className="text-sm text-red-600">{fieldErrors.password}</p>
              )}
              <div className="flex flex-wrap gap-2 pt-2">
                {passwordRequirements.map((requirement) => {
                  const met = requirement.test(formState.password);
                  return (
                    <Badge key={requirement.id} variant={met ? 'success' : 'neutral'} pill>
                      {requirement.label}
                    </Badge>
                  );
                })}
              </div>
            </div>

            <div className="space-y-1">
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                Confirm password
              </label>
              <Input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                autoComplete="new-password"
                required
                value={formState.confirmPassword}
                onChange={handleChange}
                className="mt-1"
                isInvalid={Boolean(fieldErrors.confirmPassword)}
                placeholder="••••••••"
                disabled={isLoading}
                variant="default"
              />
              {fieldErrors.confirmPassword && (
                <p className="text-sm text-red-600">{fieldErrors.confirmPassword}</p>
              )}
            </div>

            <Button type="submit" className="w-full" isLoading={isLoading} variant="primary">
              Register
            </Button>
          </form>

          <div className="text-center text-sm text-gray-600">
            By creating an account you agree to our{' '}
            <a href="/terms" className="font-medium text-blue-600 hover:text-blue-500">
              Terms of Service
            </a>{' '}
            and{' '}
            <a href="/privacy" className="font-medium text-blue-600 hover:text-blue-500">
              Privacy Policy
            </a>
            .
          </div>

          <div className="text-center text-sm text-gray-700">
            Already have an account?{' '}
            <Link href="/login" className="font-medium text-blue-600 hover:text-blue-500">
              Sign in
            </Link>
          </div>
        </div>
      </Card>
    </div>
  );
}
