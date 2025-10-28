// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.

import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { isBrowser, prefersReducedMotion } from '../utils/environment';

const navItems = [
  { label: 'Product', target: 'product' },
  { label: 'Why Ninaivalaigal', target: 'why' },
  { label: 'How It Works', target: 'how' },
  { label: 'Outcomes', target: 'outcomes' },
];

interface MarketingNavigationProps {
  activeSection?: string;
  onNavigate?: (section: string) => void;
}

export function MarketingNavigation({ activeSection, onNavigate }: MarketingNavigationProps) {
  const [isOpen, setIsOpen] = useState(false);
  const headerRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!isBrowser) {
      return;
    }

    const element = headerRef.current;
    if (!element) {
      return;
    }

    let frameId: number | null = null;

    const assignHeight = () => {
      if (!headerRef.current) {
        return;
      }
      const { height } = headerRef.current.getBoundingClientRect();
      document.documentElement.style.setProperty('--marketing-nav-height', `${height}px`);
    };

    const scheduleAssign = () => {
      if (frameId !== null) {
        window.cancelAnimationFrame(frameId);
      }
      frameId = window.requestAnimationFrame(assignHeight);
    };

    scheduleAssign();

    window.addEventListener('resize', scheduleAssign);

    let resizeObserver: ResizeObserver | null = null;
    if (typeof window.ResizeObserver !== 'undefined') {
      resizeObserver = new window.ResizeObserver(scheduleAssign);
      resizeObserver.observe(element);
    }

    return () => {
      if (frameId !== null) {
        window.cancelAnimationFrame(frameId);
      }
      window.removeEventListener('resize', scheduleAssign);
      resizeObserver?.disconnect();
    };
  }, [isOpen]);

  const handleNavigate = (section: string) => {
    onNavigate?.(section);
    if (!isBrowser) {
      return;
    }
    const element = document.getElementById(section);
    if (element) {
      element.scrollIntoView({
        behavior: prefersReducedMotion() ? 'auto' : 'smooth',
        block: 'start',
      });
    }
  };

  return (
    <header
      ref={headerRef}
      className="fixed top-0 z-40 w-full border-b border-white/5 bg-[#05070f]/85 backdrop-blur-md transition-[background-color,transform] duration-300"
    >
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-6 py-5 lg:px-8">
        <Link to="/" className="flex items-center gap-3" aria-label="Ninaivalaigal">
          <div className="brand-gradient flex h-12 w-12 items-center justify-center rounded-2xl shadow-lg shadow-indigo-500/30">
            <span className="text-[1.45rem] font-semibold text-white" aria-hidden="true">நி</span>
          </div>
          <div className="flex flex-col text-left">
            <span className="text-base font-semibold tracking-wide text-slate-100">
              Ninaivalaigal <span lang="ta" className="ml-1 font-medium tracking-normal text-slate-300/85">(நினைவலைகள்)</span>
            </span>
            <span className="text-xs uppercase tracking-[0.22em] text-slate-400">Exponential Memory OS</span>
          </div>
        </Link>
        <nav className="hidden items-center gap-9 text-sm font-semibold lg:flex">
          {navItems.map((item) => {
            const isActive = activeSection === item.target;
            return (
              <button
                key={item.target}
                type="button"
                onClick={() => handleNavigate(item.target)}
                className={`relative px-1 pb-1 text-slate-300 transition-colors duration-200 hover:text-white/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400/70 focus-visible:text-white ${
                  isActive ? 'text-white' : ''
                }`}
              >
                {item.label}
                <span
                  className={`absolute bottom-0 left-0 h-0.5 w-full rounded-full bg-indigo-400 transition-opacity duration-200 ${
                    isActive ? 'opacity-100' : 'opacity-0'
                  }`}
                />
              </button>
            );
          })}
        </nav>

        <div className="hidden items-center gap-3 lg:flex">
          <Link
            to="/login"
            className="rounded-full border border-white/10 px-4 py-2 text-sm font-semibold text-slate-200 transition-transform duration-300 ease-[cubic-bezier(.4,0,.2,1)] hover:-translate-y-1 hover:border-white/25 hover:text-white focus-visible:-translate-y-1 focus-visible:border-white/35 focus-visible:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400/60 active:translate-y-0 active:brightness-95"
          >
            Sign in
          </Link>
          <Link
            to="/signup"
            className="brand-gradient inline-flex items-center justify-center rounded-full px-5 py-2 text-sm font-semibold text-white shadow-lg shadow-indigo-500/30 transition-transform duration-300 ease-[cubic-bezier(.4,0,.2,1)] hover:-translate-y-1 hover:shadow-indigo-500/40 focus-visible:-translate-y-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400/60 active:translate-y-0 active:shadow-indigo-500/30 active:brightness-95"
          >
            Start free trial
          </Link>
        </div>

        <button
          type="button"
          aria-expanded={isOpen}
          aria-controls="marketing-menu"
          className="inline-flex items-center justify-center rounded-xl border border-white/10 px-3 py-2 text-sm font-semibold text-slate-200 transition hover:border-white/25 hover:text-white lg:hidden"
          onClick={() => setIsOpen((prev) => !prev)}
        >
          {isOpen ? 'Close' : 'Menu'}
        </button>
      </div>

      {isOpen && (
        <div
          id="marketing-menu"
          className="mx-6 mt-4 space-y-6 rounded-3xl border border-white/10 bg-slate-950/85 p-6 backdrop-blur-xl shadow-2xl shadow-slate-900/50 lg:hidden"
        >
          <nav className="flex flex-col gap-4 text-sm font-semibold text-slate-200">
            {navItems.map((item) => (
              <button
                key={item.target}
                type="button"
                onClick={() => {
                  handleNavigate(item.target);
                  setIsOpen(false);
                }}
                className="rounded-xl px-4 py-3 text-left transition hover:bg-white/5"
              >
                {item.label}
              </button>
            ))}
          </nav>
          <div className="flex flex-col gap-3">
            <Link
              to="/login"
              onClick={() => setIsOpen(false)}
              className="rounded-xl border border-white/10 px-4 py-3 text-center text-sm font-semibold text-slate-200 transition hover:border-white/25 hover:bg-white/5 hover:text-white"
            >
              Sign in
            </Link>
            <Link
              to="/signup"
              onClick={() => setIsOpen(false)}
              className="brand-gradient inline-flex items-center justify-center rounded-xl px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-500/30 transition hover:shadow-indigo-500/40"
            >
              Start free trial
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
