// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// Team-specific navigation sidebar component
// Provides quick access to all team management pages

import { Link, useLocation, useParams } from 'react-router-dom';

interface TeamNavigationProps {
  teamId?: string;
  teamName?: string;
  className?: string;
}

export function TeamNavigation({ teamId, teamName, className = '' }: TeamNavigationProps) {
  const location = useLocation();
  const params = useParams();
  const currentTeamId = teamId || params.teamId;

  const isActive = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  const navItems = [
    { path: '/team/dashboard', label: 'Dashboard', icon: '📊', requiresTeam: false },
    { path: '/team/create', label: 'Create Team', icon: '➕', requiresTeam: false },
    { path: '/team/billing', label: 'Billing', icon: '💳', requiresTeam: true },
    { path: '/team/billing/payment-method', label: 'Payment Method', icon: '💳', requiresTeam: true, parent: '/team/billing' },
    { path: '/team/billing/invoices', label: 'Invoices', icon: '📄', requiresTeam: true, parent: '/team/billing' },
    { path: '/team/usage', label: 'Usage Analytics', icon: '📈', requiresTeam: true },
    ...(currentTeamId ? [
      { path: `/team/${currentTeamId}/invite`, label: 'Invite Members', icon: '👥', requiresTeam: true },
      { path: `/team/${currentTeamId}/upgrade`, label: 'Upgrade to Org', icon: '🚀', requiresTeam: true },
    ] : []),
  ];

  // Filter based on whether we have a team context
  const visibleItems = navItems.filter(item => {
    if (item.parent && isActive(item.parent)) {
      return true; // Show child items when parent is active
    }
    if (item.requiresTeam && !currentTeamId) {
      return false; // Hide team-specific items without team context
    }
    return true;
  });

  return (
    <aside className={`bg-gray-800/50 backdrop-blur-sm border-r border-gray-700/50 min-h-screen w-64 ${className}`}>
      <div className="p-4 border-b border-gray-700/50">
        <h2 className="text-lg font-semibold text-white mb-1">
          {teamName ? `${teamName}` : 'Team'}
        </h2>
        <p className="text-xs text-slate-400">Management</p>
      </div>

      <nav className="p-2 space-y-1">
        {visibleItems.map((item) => {
          const active = isActive(item.path);
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`
                flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-all
                ${
                  active
                    ? 'bg-indigo-600 text-white shadow-lg'
                    : 'text-gray-300 hover:text-white hover:bg-gray-700/50'
                }
              `}
            >
              <span className="text-lg">{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="absolute bottom-0 w-64 p-4 border-t border-gray-700/50">
        <Link
          to="/teams"
          className="flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium text-gray-300 hover:text-white hover:bg-gray-700/50 transition"
        >
          <span>←</span>
          <span>Back to Teams</span>
        </Link>
      </div>
    </aside>
  );
}
