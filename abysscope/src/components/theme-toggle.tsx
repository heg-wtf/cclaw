"use client";

import { useTheme } from "next-themes";
import { useSyncExternalStore } from "react";

function useHydrated() {
  return useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );
}

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const mounted = useHydrated();

  if (!mounted) return null;

  return (
    <button
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
      className="relative inline-flex h-7 w-14 items-center rounded-full bg-muted transition-colors"
      title={theme === "dark" ? "Switch to light" : "Switch to dark"}
    >
      <span
        className={`inline-flex h-5 w-5 items-center justify-center rounded-full bg-background shadow transition-transform text-xs ${
          theme === "dark" ? "translate-x-8" : "translate-x-1"
        }`}
      >
        {theme === "dark" ? "🌙" : "☀️"}
      </span>
    </button>
  );
}
