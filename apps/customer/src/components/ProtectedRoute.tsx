// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// Route guard that enforces authenticated access.

import { ReactNode } from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../lib/authContext';

interface ProtectedRouteProps {
  redirectTo?: string;
  children?: ReactNode;
}

export default function ProtectedRoute({ redirectTo = '/login', children }: ProtectedRouteProps) {
  const location = useLocation();
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 text-slate-300">
        <div className="flex flex-col items-center space-y-3">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
          <span className="text-sm uppercase tracking-[0.2em]">Loading</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to={redirectTo} replace state={{ from: location }} />;
  }

  if (children) {
    return <>{children}</>;
  }

  return <Outlet />;
}
