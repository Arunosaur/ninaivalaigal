import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Theme = "light" | "dark" | "system";

export type ThemeState = {
  theme: Theme;
  setTheme: (theme: Theme) => void;
};

export const useThemeStore = create<ThemeState>()(
  persist<ThemeState>(
    (set) => ({
      theme: "system",
      setTheme: (theme: Theme) => set({ theme })
    }),
    {
      name: "nina-theme",
      version: 1
    }
  )
);
