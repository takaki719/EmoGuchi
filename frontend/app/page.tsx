'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const [activeTab, setActiveTab] = useState<'create' | 'join'>('create');
  const [roomId, setRoomId] = useState('');
  const [playerName, setPlayerName] = useState('');
  const [customRoomId, setCustomRoomId] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const router = useRouter();

  const createRoom = async () => {
    setIsCreating(true);
    try {
      const requestBody: any = {
        mode: 'basic',
        vote_type: '4choice',
        speaker_order: 'sequential',
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
      localStorage.setItem('hostToken', data.hostToken);
      router.push(`/room/${data.roomId}?name=${encodeURIComponent(playerName)}&host=true`);
    } catch (error: any) {
      console.error('Error creating room:', error);
      alert(`ルームの作成に失敗しました: ${error.message}`);
    } finally {
      setIsCreating(false);
    }
  };

  const joinRoom = () => {
    if (!roomId.trim() || !playerName.trim()) {
      alert('合言葉とプレイヤー名を入力してください');
      return;
    }
    router.push(`/room/${roomId.trim()}?name=${encodeURIComponent(playerName)}`);
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

          {/* Tab Navigation */}
          <div className="flex bg-gray-100 rounded-xl p-1 mb-6">
            <button
              onClick={() => setActiveTab('create')}
              className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all ${
                activeTab === 'create'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              ルームを作成
            </button>
            <button
              onClick={() => setActiveTab('join')}
              className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all ${
                activeTab === 'join'
                  ? 'bg-white text-green-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              ルームに参加
            </button>
          </div>

          {/* Create Room Tab */}
          {activeTab === 'create' && (
            <div className="space-y-4">
              <div>
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
                  空欄の場合は自動生成されます
                </p>
              </div>
              
              <button
                onClick={createRoom}
                disabled={!playerName.trim() || isCreating}
                className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white py-4 px-6 rounded-xl hover:from-blue-700 hover:to-blue-800 disabled:from-gray-400 disabled:to-gray-400 disabled:cursor-not-allowed transition-all font-medium text-lg shadow-lg"
              >
                {isCreating ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    作成中...
                  </div>
                ) : (
                  '🎮 ルームを作成'
                )}
              </button>
            </div>
          )}

          {/* Join Room Tab */}
          {activeTab === 'join' && (
            <div className="space-y-4">
              <div>
                <label htmlFor="roomId" className="block text-sm font-medium text-gray-700 mb-2">
                  合言葉
                </label>
                <input
                  type="text"
                  id="roomId"
                  value={roomId}
                  onChange={(e) => setRoomId(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all"
                  placeholder="合言葉を入力"
                  maxLength={20}
                />
              </div>
              
              <button
                onClick={joinRoom}
                disabled={!roomId.trim() || !playerName.trim()}
                className="w-full bg-gradient-to-r from-green-600 to-green-700 text-white py-4 px-6 rounded-xl hover:from-green-700 hover:to-green-800 disabled:from-gray-400 disabled:to-gray-400 disabled:cursor-not-allowed transition-all font-medium text-lg shadow-lg"
              >
                🚪 ルームに参加
              </button>
            </div>
          )}

          {/* Footer */}
          <div className="mt-8 text-center text-sm text-gray-500">
            <p>感情を演技で表現し、みんなで推理するゲームです</p>
          </div>
        </div>
      </div>
    </div>
  );
}