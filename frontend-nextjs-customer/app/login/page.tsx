// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
'use client';

import { useRouter } from 'next/navigation';
import { LoginForm } from '../../components/LoginForm';

export default function LoginPage() {
  const router = useRouter();

  const handleSuccess = () => {
    router.push('/dashboard');
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-md space-y-8 rounded-lg bg-white p-8 shadow">
        <div className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-gray-900">
            Welcome Back
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Sign in to your Ninaivalaigal account
          </p>
        </div>

        <LoginForm onSuccess={handleSuccess} />

        <div className="text-center text-sm text-gray-600">
          Don&apos;t have an account?{' '}
          <a href="/signup" className="font-medium text-blue-600 hover:text-blue-500">
            Sign up
          </a>
        </div>
      </div>
    </div>
  );
}
