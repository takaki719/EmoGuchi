import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type Locale = 'ja' | 'en';

interface LocaleState {
  locale: Locale;
  setLocale: (locale: Locale) => void;
}

export const useLocaleStore = create<LocaleState>()(
  persist(
    (set) => ({
      locale: 'ja', // デフォルトは日本語
      setLocale: (locale: Locale) => set({ locale }),
    }),
    {
      name: 'emoguchi-locale',
    }
  )
);