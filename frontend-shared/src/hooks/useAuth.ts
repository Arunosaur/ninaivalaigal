import { useCallback } from "react";
import { fetchApi } from "../lib/api";
import type { Session } from "../lib/schemas";
import { useAuthStore } from "../state/authStore";

export function useAuth() {
  const { session, setSession, clearSession } = useAuthStore();

  const login = useCallback(
    async (email: string, password: string) => {
      const result = await fetchApi<{ session: Session }>("/auth/login", {
        baseUrl: "/api",
        headers: {
          Authorization: `Basic ${btoa(`${email}:${password}`)}`
        }
      });

      setSession(result.session);
      return result.session;
    },
    [setSession]
  );

  const logout = useCallback(async () => {
    await fetchApi<void>("/auth/logout");
    clearSession();
  }, [clearSession]);

  return {
    session,
    isAuthenticated: Boolean(session),
    login,
    logout
  };
}
