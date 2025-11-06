// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * Shared Navigation Component
 *
 * Provides consistent navigation across all customer-facing pages.
 */
import { useState, useRef } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../lib/authContext';

interface NavigationProps {
  variant?: 'default' | 'dark' | 'transparent';
  className?: string;
}

export function Navigation({ variant = 'default', className = '' }: NavigationProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, clearAuthState } = useAuth();
  const navRef = useRef<HTMLElement>(null);
  const navItemsRef = useRef<(HTMLAnchorElement | null)[]>([]);

  // Check if we're on a team or settings sub-page to highlight parent nav
  const isTeamPage = location.pathname.startsWith('/team/');
  const isSettingsPage = location.pathname.startsWith('/settings') || location.pathname === '/discounts';

  const isActive = (path: string) => {
    if (path === '/teams' && isTeamPage) return true;
    if (path === '/settings' && isSettingsPage) return true;
    return location.pathname === path;
  };

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: '📊' },
    { path: '/memory-browser', label: 'Memory Browser', icon: '📖' },
    { path: '/teams', label: 'Teams', icon: '👥' },
    { path: '/settings', label: 'Settings', icon: '⚙️' },
  ];

  const getNavStyle = () => {
    switch (variant) {
      case 'dark':
        return 'bg-gray-800/50 backdrop-blur-sm border-b border-gray-700/50';
      case 'transparent':
        return 'bg-transparent';
      default:
        return 'bg-gradient-to-r from-purple-600 to-purple-800 shadow-lg';
    }
  };

  const handleLogout = () => {
    clearAuthState();
    navigate('/login', { replace: true });
  };

  const handleKeyDown = (event: React.KeyboardEvent, index: number) => {
    if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') {
      event.preventDefault();
      const nextIndex = event.key === 'ArrowRight'
        ? Math.min(index + 1, navItems.length - 1)
        : Math.max(index - 1, 0);
      navItemsRef.current[nextIndex]?.focus();
    } else if (event.key === 'Home') {
      event.preventDefault();
      navItemsRef.current[0]?.focus();
    } else if (event.key === 'End') {
      event.preventDefault();
      navItemsRef.current[navItems.length - 1]?.focus();
    }
  };

  const userLabel = user?.name || user?.email;

  return (
    <nav
      ref={navRef}
      className={`${getNavStyle()} ${className} sticky top-0 z-50`}
      role="navigation"
      aria-label="Main navigation"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo and Brand */}
          <div className="flex items-center">
            <Link
              to="/dashboard"
              className="flex items-center space-x-3 hover:opacity-80 transition-all duration-300 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-purple-600 rounded"
              aria-label="Ninaivalaigal - Go to dashboard"
            >
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center shadow-lg transition-transform duration-300 hover:rotate-3">
                <span className="text-white font-semibold text-[1.35rem]" aria-hidden="true">நி</span>
              </div>
              <h1 className="text-2xl font-bold text-white transition-all duration-300">
                Ninaivalaigal <span lang="ta" className="ml-2 text-xl font-medium text-white/85">(நினைவலைகள்)</span>
              </h1>
            </Link>
          </div>

          {/* Navigation Links */}
          <ul className="flex items-center space-x-1 list-none" role="menubar">
            {navItems.map((item, index) => (
              <li key={item.path} role="none">
                <Link
                  ref={(el) => {
                    navItemsRef.current[index] = el;
                  }}
                  to={item.path}
                  role="menuitem"
                  aria-current={isActive(item.path) ? 'page' : undefined}
                  onKeyDown={(e) => handleKeyDown(e, index)}
                  className={`
                    flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300
                    transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-purple-600
                    ${
                      isActive(item.path)
                        ? 'bg-white/20 text-white border border-white/30 shadow-lg scale-105'
                        : 'text-white/80 hover:text-white hover:bg-white/10'
                    }
                  `}
                  aria-label={`Navigate to ${item.label}`}
                >
                  <span className="transition-transform duration-300" aria-hidden="true">{item.icon}</span>
                  <span>{item.label}</span>
                </Link>
              </li>
            ))}
          </ul>

          {/* User Actions */}
          <div className="flex items-center space-x-4 text-white/80">
            {userLabel ? (
              <span className="text-sm transition-opacity duration-300 hover:opacity-100 opacity-90" aria-label={`Logged in as ${userLabel}`}>
                {userLabel}
              </span>
            ) : null}
            <button
              onClick={handleLogout}
              className="hover:text-white hover:bg-white/10 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-purple-600"
              aria-label="Log out of your account"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}

/**
 * Alternative: Sidebar Navigation
 * For apps that need a persistent sidebar
 */
export function SidebarNavigation() {
  const location = useLocation();
  const navigate = useNavigate();
  const { clearAuthState, user } = useAuth();

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: '📊' },
    { path: '/memory-browser', label: 'Memory Browser', icon: '📖' },
    { path: '/teams', label: 'Teams', icon: '👥' },
    { path: '/settings', label: 'Settings', icon: '⚙️' },
  ];

  const handleLogout = () => {
    clearAuthState();
    navigate('/login', { replace: true });
  };

  return (
    <aside className="w-64 bg-gray-800 border-r border-gray-700 min-h-screen">
      {/* Logo */}
      <div className="p-6 border-b border-gray-700">
        <Link to="/dashboard" className="flex items-center space-x-3" aria-label="Ninaivalaigal">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-semibold text-[1.35rem]" aria-hidden="true">நி</span>
          </div>
          <h1 className="text-xl font-bold text-white">
            Ninaivalaigal <span lang="ta" className="ml-2 text-lg font-medium text-white/85">(நினைவலைகள்)</span>
          </h1>
        </Link>
      </div>

      {/* Navigation Items */}
      <nav className="p-4 space-y-2">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`
              flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium transition-all
              ${
                isActive(item.path)
                  ? 'bg-purple-600 text-white shadow-lg'
                  : 'text-gray-300 hover:text-white hover:bg-gray-700'
              }
            `}
          >
            <span className="text-xl">{item.icon}</span>
            <span>{item.label}</span>
          </Link>
        ))}
      </nav>

      {/* User Section */}
      <div className="absolute bottom-0 w-64 p-4 border-t border-gray-700">
        {user?.email ? (
          <div className="mb-2 text-xs uppercase tracking-[0.18em] text-gray-500">{user.email}</div>
        ) : null}
        <button
          onClick={handleLogout}
          className="w-full text-gray-300 hover:text-white hover:bg-gray-700 px-4 py-2 rounded-lg text-sm font-medium transition-all"
        >
          Logout
        </button>
      </div>
    </aside>
  );
}

/**
 * Mobile Navigation
 * Responsive hamburger menu for mobile devices
 */
export function MobileNavigation() {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { clearAuthState } = useAuth();

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: '📊' },
    { path: '/memory-browser', label: 'Memory Browser', icon: '📖' },
    { path: '/teams', label: 'Teams', icon: '👥' },
    { path: '/settings', label: 'Settings', icon: '⚙️' },
  ];

  const handleLogout = () => {
    clearAuthState();
    navigate('/login', { replace: true });
  };

  return (
    <>
      {/* Mobile Header */}
      <nav className="bg-gradient-to-r from-purple-600 to-purple-800 shadow-lg md:hidden">
        <div className="px-4 py-3 flex items-center justify-between">
          <Link to="/dashboard" className="flex items-center space-x-2" aria-label="Ninaivalaigal">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-semibold text-lg" aria-hidden="true">நி</span>
            </div>
            <h1 className="text-lg font-bold text-white">
              Ninaivalaigal <span lang="ta" className="ml-1 text-base font-medium text-white/80">(நினைவலைகள்)</span>
            </h1>
          </Link>
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="text-white p-2 rounded-lg hover:bg-white/10 transition"
          >
            {isOpen ? '✕' : '☰'}
          </button>
        </div>

        {/* Mobile Menu */}
        {isOpen && (
          <div className="px-4 py-4 bg-gray-900 border-t border-gray-700">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setIsOpen(false)}
                className={`
                  flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium mb-2 transition
                  ${
                    isActive(item.path)
                      ? 'bg-purple-600 text-white'
                      : 'text-gray-300 hover:text-white hover:bg-gray-800'
                  }
                `}
              >
                <span className="text-xl">{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            ))}
            <button
              onClick={handleLogout}
              className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium text-gray-300 hover:text-white hover:bg-gray-800 transition mt-4"
            >
              <span className="text-xl">🚪</span>
              <span>Logout</span>
            </button>
          </div>
        )}
      </nav>
    </>
  );
}
