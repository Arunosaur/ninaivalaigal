/**
 * Zustand auth store - shared across customer and admin apps
 * Syncs with NextAuth.js session
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  email: string;
  role: 'customer' | 'admin' | 'staff';
  name?: string;
  avatar?: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  // Actions
  setUser: (user: User | null) => void;
  logout: () => void;
  updateProfile: (updates: Partial<User>) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      isLoading: true,

      setUser: (user) =>
        set({
          user,
          isAuthenticated: !!user,
          isLoading: false,
        }),

      logout: () =>
        set({
          user: null,
          isAuthenticated: false,
          isLoading: false,
        }),

      updateProfile: (updates) =>
        set((state) => ({
          user: state.user ? { ...state.user, ...updates } : null,
        })),
    }),
    {
      name: 'ninaivalaigal-auth',
      partialize: (state) => ({ user: state.user }), // Only persist user data
    }
  )
);

/**
 * Usage in components:
 *
 * import { useAuthStore } from '@ninaivalaigal/ui-components/state/authStore';
 *
 * const { user, isAuthenticated, setUser, logout } = useAuthStore();
 */
