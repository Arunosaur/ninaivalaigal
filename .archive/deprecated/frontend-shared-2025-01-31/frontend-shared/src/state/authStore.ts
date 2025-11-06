// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { create } from "zustand";
import { persist } from "zustand/middleware";
import { sessionSchema, type Session } from "../lib/schemas";

export type AuthState = {
  session: Session | null;
  setSession: (session: Session | null) => void;
  clearSession: () => void;
};

export const useAuthStore = create<AuthState>()(
  persist<AuthState>(
    (set) => ({
      session: null,
      setSession: (data: Session | null) => {
        const parseResult = sessionSchema.safeParse(data);
        if (!parseResult.success) {
          console.warn("Invalid session payload", parseResult.error.flatten());
          return;
        }
        set({ session: parseResult.data });
      },
      clearSession: () => set({ session: null })
    }),
    {
      name: "nina-auth-session"
    }
  )
);
