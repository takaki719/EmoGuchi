'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useLocaleStore } from '@/stores/localeStore';
import { translations } from '@/lib/translations';
import LanguageSwitcher from '@/components/LanguageSwitcher';
import { getApiUrl } from '@/utils/api';
import { getSavedPlayerName } from '@/utils/playerStorage';

// Edge Runtime 対応
export const runtime = 'edge';

export default function Home() {
  const [playerName, setPlayerName] = useState('');
  const [customRoomId, setCustomRoomId] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [nameError, setNameError] = useState('');
  const [roomIdError, setRoomIdError] = useState('');
  const router = useRouter();
  const { locale } = useLocaleStore();
  const t = translations[locale];

  // 保存された名前を自動入力
  useEffect(() => {
    const savedName = getSavedPlayerName();
    if (savedName) {
      setPlayerName(savedName);
    }
  }, []);

  const validateInputs = () => {
    let isValid = true;
    setNameError('');
    setRoomIdError('');

    if (!playerName.trim()) {
      setNameError('プレイヤー名を入力してください');
      isValid = false;
    } else if (playerName.trim().length < 2) {
      setNameError('プレイヤー名は2文字以上で入力してください');
      isValid = false;
    }

    if (customRoomId.trim() && customRoomId.trim().length < 3) {
      setRoomIdError('合言葉は3文字以上で入力してください');
      isValid = false;
    }

    return isValid;
  };

  const createRoom = async () => {
    if (!validateInputs()) return;
    
    setIsCreating(true);
    try {
      const requestBody: any = {
        mode: 'basic',
        vote_type: '4choice',
        speaker_order: 'sequential',
        max_rounds: 1,
      };
      
      // Add custom room ID if provided
      if (customRoomId.trim()) {
        requestBody.room_id = customRoomId.trim();
      }

      const response = await fetch(`${getApiUrl()}/api/v1/rooms`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to create room' }));
        throw new Error(errorData.detail || 'Failed to create room');
      }

      const data = await response.json();
      
      // Only set host token and host flag for new rooms
      if (!data.isExistingRoom) {
        localStorage.setItem('hostToken', data.hostToken);
        router.push(`/room/${encodeURIComponent(data.roomId)}?name=${encodeURIComponent(playerName)}&host=true`);
      } else {
        // For existing rooms, join as regular participant
        router.push(`/room/${encodeURIComponent(data.roomId)}?name=${encodeURIComponent(playerName)}`);
      }
    } catch (error: any) {
      console.error('Error creating room:', error);
      alert(`${locale === 'ja' ? 'ルームの作成に失敗しました' : 'Failed to create room'}: ${error.message}`);
    } finally {
      setIsCreating(false);
    }
  };


  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:from-slate-900 dark:via-slate-800 dark:to-purple-900 transition-colors duration-300">
      <div className="max-w-md w-full bg-white dark:bg-slate-800 rounded-2xl shadow-2xl dark:shadow-slate-900/50 overflow-hidden relative backdrop-blur-sm border border-white/20 dark:border-slate-700/50 transform hover:scale-[1.02] transition-all duration-300">
        {/* Language Switcher */}
        <div className="absolute top-2 right-2 sm:top-4 sm:right-4 z-10">
          <LanguageSwitcher />
        </div>

        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white p-8 text-center relative overflow-hidden">
          <div className="absolute inset-0 bg-black/10 backdrop-blur-sm"></div>
          <div className="relative z-10">
            <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-white to-blue-100 bg-clip-text text-transparent drop-shadow-lg">{t.home.title}</h1>
            <p className="text-blue-100/90 text-lg font-medium">{t.home.subtitle}</p>
          </div>
        </div>

        <div className="p-8">
          {/* Player Name Input */}
          <div className="mb-6">
            <label htmlFor="playerName" className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              {t.home.playerName}
            </label>
            <input
              type="text"
              id="playerName"
              value={playerName}
              onChange={(e) => {
                setPlayerName(e.target.value);
                if (nameError) setNameError('');
              }}
              className={`w-full px-4 py-3 border ${nameError ? 'border-red-500 dark:border-red-400' : 'border-gray-300 dark:border-gray-600'} bg-white dark:bg-slate-700 text-gray-900 dark:text-white rounded-xl focus:outline-none focus:ring-2 ${nameError ? 'focus:ring-red-500' : 'focus:ring-blue-500 dark:focus:ring-blue-400'} focus:border-transparent transition-all duration-200 hover:border-gray-400 dark:hover:border-gray-500`}
              placeholder={t.home.playerNamePlaceholder}
              maxLength={20}
            />
            {nameError && (
              <div className="text-red-500 dark:text-red-400 text-sm mt-1 animate-fade-in">
                {nameError}
              </div>
            )}
          </div>

          {/* Room Input */}
          <div className="mb-6">
            <label htmlFor="customRoomId" className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              {t.home.customRoomId}
            </label>
            <input
              type="text"
              id="customRoomId"
              value={customRoomId}
              onChange={(e) => {
                setCustomRoomId(e.target.value);
                if (roomIdError) setRoomIdError('');
              }}
              className={`w-full px-4 py-3 border ${roomIdError ? 'border-red-500 dark:border-red-400' : 'border-gray-300 dark:border-gray-600'} bg-white dark:bg-slate-700 text-gray-900 dark:text-white rounded-xl focus:outline-none focus:ring-2 ${roomIdError ? 'focus:ring-red-500' : 'focus:ring-blue-500 dark:focus:ring-blue-400'} focus:border-transparent transition-all duration-200 hover:border-gray-400 dark:hover:border-gray-500`}
              placeholder={t.home.customRoomIdPlaceholder}
              maxLength={20}
            />
            {roomIdError && (
              <div className="text-red-500 dark:text-red-400 text-sm mt-1 animate-fade-in">
                {roomIdError}
              </div>
            )}
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
              {locale === 'ja' ? '空欄で新規作成、入力で既存ルームに参加' : 'Leave blank to create new room, enter to join existing room'}
            </p>
          </div>

          
          {/* Action Buttons */}
          <div className="space-y-4">
            <button
              onClick={createRoom}
              disabled={!playerName.trim() || isCreating || !!nameError || !!roomIdError}
              className="group w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white py-4 px-6 rounded-xl disabled:from-gray-400 disabled:to-gray-400 disabled:cursor-not-allowed disabled:opacity-50 transition-all duration-200 font-medium text-lg shadow-lg hover:shadow-xl transform hover:scale-[1.02] active:scale-[0.98] focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-slate-800 relative overflow-hidden"
            >
              <div className="absolute inset-0 bg-white/20 transform -skew-x-12 -translate-x-full group-hover:translate-x-full transition-transform duration-700 ease-out"></div>
              <div className="relative z-10">
                {isCreating ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    <span className="animate-pulse">
                      {customRoomId.trim() ? 
                        (locale === 'ja' ? '参加中...' : 'Joining...') : 
                        (locale === 'ja' ? '作成中...' : 'Creating...')
                      }
                    </span>
                  </div>
                ) : (
                  <span className="flex items-center justify-center">
                    <span className="mr-2 transform group-hover:scale-110 transition-transform">
                      {customRoomId.trim() ? '🚪' : '🎮'}
                    </span>
                    {customRoomId.trim() ? t.home.joinRoom : t.home.createRoom}
                  </span>
                )}
              </div>
            </button>

            {/* Solo Mode Button */}
            <button
              onClick={() => router.push('/solo')}
              className="group w-full bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white py-4 px-6 rounded-xl transition-all duration-200 font-medium text-lg shadow-lg hover:shadow-xl transform hover:scale-[1.02] active:scale-[0.98] focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 dark:focus:ring-offset-slate-800 relative overflow-hidden"
            >
              <div className="absolute inset-0 bg-white/20 transform -skew-x-12 -translate-x-full group-hover:translate-x-full transition-transform duration-700 ease-out"></div>
              <div className="relative z-10 flex items-center justify-center">
                <span className="mr-2 transform group-hover:rotate-12 transition-transform duration-200">🎭</span>
                {locale === 'ja' ? 'ソロ演技モード' : 'Solo Acting Mode'}
              </div>
            </button>
          </div>

          {/* Footer */}
          <div className="mt-8 text-center text-sm text-gray-500 dark:text-gray-400">
            <p>
              {locale === 'ja' ? (
                <>スピーカーは指定された感情とセリフで演技し、<br/>リスナーは感情を推理するゲームです</>
              ) : (
                <>Speakers perform with given emotions and scripts,<br/>Listeners guess the emotions</>
              )}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}