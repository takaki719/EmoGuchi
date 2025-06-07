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
        className="flex items-center gap-1 sm:gap-2 px-2 py-1.5 sm:px-3 sm:py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors text-xs sm:text-sm"
        title={t.common.language}
      >
        <span className="text-sm sm:text-base">⚙️</span>
        <span className="hidden sm:inline">{locale === 'ja' ? '日本語' : 'English'}</span>
        <span className="sm:hidden text-xs">{locale === 'ja' ? 'JP' : 'EN'}</span>
      </button>
    </div>
  );
}