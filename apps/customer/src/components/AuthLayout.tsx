// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//

import { ReactNode } from 'react';

interface AuthLayoutProps {
  children: ReactNode;
}

export default function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#050b1a]">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-x-0 top-[-10%] h-[520px] bg-[radial-gradient(circle,_rgba(99,102,241,0.35)_0%,_rgba(5,11,26,0)_60%)]" />
        <div className="absolute inset-x-0 bottom-[-30%] h-[480px] bg-[radial-gradient(circle,_rgba(236,72,153,0.12)_0%,_rgba(5,11,26,0)_70%)]" />
      </div>

      <div className="relative w-full max-w-md px-6">
        <div className="glass-surface gradient-outline rounded-[28px] p-[1px]">
          <div className="rounded-[26px] bg-slate-950/60 p-10 shadow-[0_40px_60px_-45px_rgba(15,23,42,0.95)]">
            <div className="mb-8 flex flex-col items-center text-center">
              <div className="brand-gradient flex h-12 w-12 items-center justify-center rounded-2xl shadow-lg shadow-indigo-500/40">
                <span className="text-[1.45rem] font-semibold text-white" aria-hidden="true">நி</span>
              </div>
              <h1 className="mt-4 text-2xl font-semibold text-white">
                Ninaivalaigal <span lang="ta" className="ml-2 text-xl font-medium text-white/85">(நினைவலைகள்)</span>
              </h1>
              <p className="mt-2 text-sm font-medium text-slate-400">
                e<sup>M</sup> — Exponential Memory System
              </p>
            </div>

            <div className="space-y-6">{children}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
