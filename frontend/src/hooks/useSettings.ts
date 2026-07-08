import { useCallback, useEffect, useState } from "react";

export interface AppSettings {
  showTimestamps: boolean;
  autoScroll: boolean;
  compactMode: boolean;
  enterToSend: boolean;
  showSources: boolean;
  backendUrl: string;
}

const STORAGE_KEY = "studybuddy_settings";

const DEFAULT_SETTINGS: AppSettings = {
  showTimestamps: true,
  autoScroll: true,
  compactMode: false,
  enterToSend: true,
  showSources: true,
  backendUrl: import.meta.env.VITE_API_URL || "http://127.0.0.1:5000",
};

function loadSettings(): AppSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      // If the stored url is the default localhost address but a production VITE_API_URL is configured, override it.
      if ((parsed.backendUrl === "http://127.0.0.1:5000" || parsed.backendUrl === "http://localhost:5000") && import.meta.env.VITE_API_URL) {
        parsed.backendUrl = import.meta.env.VITE_API_URL;
      }
      return { ...DEFAULT_SETTINGS, ...parsed };
    }
  } catch {
    /* ignore */
  }
  return DEFAULT_SETTINGS;
}

export function useSettings() {
  const [settings, setSettingsState] = useState<AppSettings>(loadSettings);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  }, [settings]);

  const updateSetting = useCallback(<K extends keyof AppSettings>(key: K, value: AppSettings[K]) => {
    setSettingsState((prev) => ({ ...prev, [key]: value }));
  }, []);

  const resetSettings = useCallback(() => {
    setSettingsState(DEFAULT_SETTINGS);
  }, []);

  return { settings, updateSetting, resetSettings };
}
