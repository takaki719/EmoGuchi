'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const [playerName, setPlayerName] = useState('');
  const [customRoomId, setCustomRoomId] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);
  const [gameMode, setGameMode] = useState<'basic' | 'advanced'>('basic');
  const [maxRounds, setMaxRounds] = useState(3);
  const [speakerOrder, setSpeakerOrder] = useState<'sequential' | 'random'>('sequential');
  const router = useRouter();

  const createRoom = async () => {
    setIsCreating(true);
    try {
      const requestBody: any = {
        mode: gameMode,
        vote_type: gameMode === 'advanced' ? '8choice' : '4choice',
        speaker_order: speakerOrder,
        max_rounds: maxRounds,
      };
      
      // Add custom room ID if provided
      if (customRoomId.trim()) {
        requestBody.room_id = customRoomId.trim();
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002'}/api/v1/rooms`, {
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
      alert(`ルームの作成に失敗しました: ${error.message}`);
    } finally {
      setIsCreating(false);
    }
  };


  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-blue-50 to-purple-50">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-8 text-center">
          <h1 className="text-4xl font-bold mb-2">🎭 EMOGUCHI</h1>
          <p className="text-blue-100">音声演技 × 感情推定ゲーム</p>
        </div>

        <div className="p-8">
          {/* Player Name Input */}
          <div className="mb-6">
            <label htmlFor="playerName" className="block text-sm font-medium text-gray-700 mb-2">
              プレイヤー名
            </label>
            <input
              type="text"
              id="playerName"
              value={playerName}
              onChange={(e) => setPlayerName(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              placeholder="あなたの名前を入力"
              maxLength={20}
            />
          </div>

          {/* Room Input */}
          <div className="mb-6">
            <label htmlFor="customRoomId" className="block text-sm font-medium text-gray-700 mb-2">
              合言葉（任意）
            </label>
            <input
              type="text"
              id="customRoomId"
              value={customRoomId}
              onChange={(e) => setCustomRoomId(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              placeholder="例: やきにく123, 遊戯王..."
              maxLength={20}
            />
            <p className="text-xs text-gray-500 mt-2">
              空欄で新規作成、入力で既存ルームに参加
            </p>
          </div>

          {/* Advanced Settings Toggle */}
          <div className="mb-6">
            <button
              type="button"
              onClick={() => setShowAdvancedSettings(!showAdvancedSettings)}
              className="w-full flex items-center justify-between px-4 py-3 border border-gray-300 rounded-xl hover:bg-gray-50 transition-all"
            >
              <span className="text-sm font-medium text-gray-700">詳細設定</span>
              <span className={`transform transition-transform ${showAdvancedSettings ? 'rotate-180' : ''}`}>
                ▼
              </span>
            </button>
          </div>

          {/* Advanced Settings Panel */}
          {showAdvancedSettings && (
            <div className="mb-6 p-4 border border-gray-200 rounded-xl bg-gray-50">
              {/* Game Mode */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  感情モード
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setGameMode('basic')}
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                      gameMode === 'basic'
                        ? 'bg-blue-600 text-white'
                        : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    基本感情 (4択)
                  </button>
                  <button
                    type="button"
                    onClick={() => setGameMode('advanced')}
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                      gameMode === 'advanced'
                        ? 'bg-blue-600 text-white'
                        : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    応用感情 (8択)
                  </button>
                </div>
              </div>

              {/* Max Rounds */}
              <div className="mb-4">
                <label htmlFor="maxRounds" className="block text-sm font-medium text-gray-700 mb-2">
                  ラウンド数
                </label>
                <select
                  id="maxRounds"
                  value={maxRounds}
                  onChange={(e) => setMaxRounds(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(num => (
                    <option key={num} value={num}>{num}周</option>
                  ))}
                </select>
              </div>

              {/* Speaker Order */}
              <div className="mb-0">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  発言順
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setSpeakerOrder('sequential')}
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                      speakerOrder === 'sequential'
                        ? 'bg-blue-600 text-white'
                        : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    順番
                  </button>
                  <button
                    type="button"
                    onClick={() => setSpeakerOrder('random')}
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                      speakerOrder === 'random'
                        ? 'bg-blue-600 text-white'
                        : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    ランダム
                  </button>
                </div>
              </div>
            </div>
          )}
          
          {/* Action Button */}
          <button
            onClick={createRoom}
            disabled={!playerName.trim() || isCreating}
            className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white py-4 px-6 rounded-xl hover:from-blue-700 hover:to-blue-800 disabled:from-gray-400 disabled:to-gray-400 disabled:cursor-not-allowed transition-all font-medium text-lg shadow-lg"
          >
            {isCreating ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                {customRoomId.trim() ? '参加中...' : '作成中...'}
              </div>
            ) : (
              customRoomId.trim() ? '🚪 ルームに参加' : '🎮 ルームを作成'
            )}
          </button>

          {/* Footer */}
          <div className="mt-8 text-center text-sm text-gray-500">
            <p>スピーカーは指定された感情とセリフで演技し、<br/>リスナーは感情を推理するゲームです</p>
          </div>
        </div>
      </div>
    </div>
  );
}