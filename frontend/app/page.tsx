'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useLocaleStore } from '@/stores/localeStore';
import { translations } from '@/lib/translations';
import LanguageSwitcher from '@/components/LanguageSwitcher';

export default function Home() {
  const [playerName, setPlayerName] = useState('');
  const [customRoomId, setCustomRoomId] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const router = useRouter();
  const { locale } = useLocaleStore();
  const t = translations[locale];

  const createRoom = async () => {
    setIsCreating(true);
    try {
      const requestBody: any = {
        mode: 'basic',
        vote_type: '4choice',
        speaker_order: 'sequential',
        max_rounds: 3,
      };
      
      // Add custom room ID if provided
      if (customRoomId.trim()) {
        requestBody.room_id = customRoomId.trim();
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/rooms`, {
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
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-blue-50 to-purple-50">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-2xl overflow-hidden relative">
        {/* Language Switcher */}
        <div className="absolute top-2 right-2 sm:top-4 sm:right-4 z-10">
          <LanguageSwitcher />
        </div>

        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-8 text-center">
          <h1 className="text-4xl font-bold mb-2">{t.home.title}</h1>
          <p className="text-blue-100">{t.home.subtitle}</p>
        </div>

        <div className="p-8">
          {/* Player Name Input */}
          <div className="mb-6">
            <label htmlFor="playerName" className="block text-sm font-medium text-gray-700 mb-2">
              {t.home.playerName}
            </label>
            <input
              type="text"
              id="playerName"
              value={playerName}
              onChange={(e) => setPlayerName(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              placeholder={t.home.playerNamePlaceholder}
              maxLength={20}
            />
          </div>

          {/* Room Input */}
          <div className="mb-6">
            <label htmlFor="customRoomId" className="block text-sm font-medium text-gray-700 mb-2">
              {t.home.customRoomId}
            </label>
            <input
              type="text"
              id="customRoomId"
              value={customRoomId}
              onChange={(e) => setCustomRoomId(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              placeholder={t.home.customRoomIdPlaceholder}
              maxLength={20}
            />
            <p className="text-xs text-gray-500 mt-2">
              {locale === 'ja' ? '空欄で新規作成、入力で既存ルームに参加' : 'Leave blank to create new room, enter to join existing room'}
            </p>
          </div>

          
          {/* Action Button */}
          <button
            onClick={createRoom}
            disabled={!playerName.trim() || isCreating}
            className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white py-4 px-6 rounded-xl hover:from-blue-700 hover:to-blue-800 disabled:from-gray-400 disabled:to-gray-400 disabled:cursor-not-allowed transition-all font-medium text-lg shadow-lg"
          >
            {isCreating ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                {customRoomId.trim() ? 
                  (locale === 'ja' ? '参加中...' : 'Joining...') : 
                  (locale === 'ja' ? '作成中...' : 'Creating...')
                }
              </div>
            ) : (
              customRoomId.trim() ? 
                `🚪 ${t.home.joinRoom}` : 
                `🎮 ${t.home.createRoom}`
            )}
          </button>

          {/* Footer */}
          <div className="mt-8 text-center text-sm text-gray-500">
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