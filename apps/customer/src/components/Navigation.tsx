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
import { useState } from 'react';
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

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: '📊' },
    { path: '/memory-browser', label: 'Memory Browser', icon: '📖' },
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

  const userLabel = user?.name || user?.email;

  return (
    <nav className={`${getNavStyle()} ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo and Brand */}
          <div className="flex items-center">
            <Link to="/dashboard" className="flex items-center space-x-3 hover:opacity-80 transition">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center shadow-lg">
                <span className="text-white font-bold text-xl">N</span>
              </div>
              <h1 className="text-2xl font-bold text-white">Ninaivalaigal</h1>
            </Link>
          </div>

          {/* Navigation Links */}
          <div className="flex items-center space-x-1">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`
                  flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all
                  ${
                    isActive(item.path)
                      ? 'bg-white/20 text-white border border-white/30 shadow-lg'
                      : 'text-white/80 hover:text-white hover:bg-white/10'
                  }
                `}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            ))}
          </div>

          {/* User Actions */}
          <div className="flex items-center space-x-4 text-white/80">
            {userLabel ? <span className="text-sm">{userLabel}</span> : null}
            <button
              onClick={handleLogout}
              className="hover:text-white hover:bg-white/10 px-4 py-2 rounded-lg text-sm font-medium transition-all"
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
        <Link to="/dashboard" className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-xl">N</span>
          </div>
          <h1 className="text-xl font-bold text-white">Ninaivalaigal</h1>
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
          <Link to="/dashboard" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold">N</span>
            </div>
            <h1 className="text-lg font-bold text-white">Ninaivalaigal</h1>
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
