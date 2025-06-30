'use client';

import { useLocaleStore } from '@/stores/localeStore';
import { translations } from '@/lib/translations';

export default function LanguageSwitcher() {
  const { locale, setLocale } = useLocaleStore();
  const t = translations[locale];

  return (
    <div className="relative">
      <button
        onClick={() => setLocale(locale === 'ja' ? 'en' : 'ja')}
        className="flex items-center gap-1 sm:gap-2 px-2 py-1.5 sm:px-3 sm:py-2 bg-white/80 dark:bg-slate-800/80 hover:bg-white dark:hover:bg-slate-700 rounded-lg transition-all duration-200 text-xs sm:text-sm backdrop-blur-sm border border-white/20 dark:border-slate-700/50 shadow-sm hover:shadow-md text-gray-700 dark:text-gray-200 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-transparent"
        title={t.common.language}
      >
        <span className="text-sm sm:text-base">🌐</span>
        <span className="hidden sm:inline">{locale === 'ja' ? '日本語' : 'English'}</span>
        <span className="sm:hidden text-xs">{locale === 'ja' ? 'JP' : 'EN'}</span>
      </button>
    </div>
  );
}