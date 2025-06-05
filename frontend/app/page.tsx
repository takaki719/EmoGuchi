'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const [roomId, setRoomId] = useState('');
  const [playerName, setPlayerName] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const router = useRouter();

  const createRoom = async () => {
    setIsCreating(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002'}/api/v1/rooms`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          mode: 'basic',
          vote_type: '4choice',
          speaker_order: 'sequential',
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create room');
      }

      const data = await response.json();
      localStorage.setItem('hostToken', data.hostToken);
      router.push(`/room/${data.roomId}?name=${encodeURIComponent(playerName)}&host=true`);
    } catch (error) {
      console.error('Error creating room:', error);
      alert('ルームの作成に失敗しました');
    } finally {
      setIsCreating(false);
    }
  };

  const joinRoom = () => {
    if (!roomId.trim() || !playerName.trim()) {
      alert('ルームIDとプレイヤー名を入力してください');
      return;
    }
    router.push(`/room/${roomId}?name=${encodeURIComponent(playerName)}`);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-xl p-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">🎭 EMOGUCHI</h1>
          <p className="text-gray-600">音声演技 × 感情推定ゲーム</p>
        </div>

        <div className="space-y-6">
          <div>
            <label htmlFor="playerName" className="block text-sm font-medium text-gray-700 mb-2">
              プレイヤー名
            </label>
            <input
              type="text"
              id="playerName"
              value={playerName}
              onChange={(e) => setPlayerName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="あなたの名前を入力"
              maxLength={20}
            />
          </div>

          <div className="border-t pt-6">
            <button
              onClick={createRoom}
              disabled={!playerName.trim() || isCreating}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {isCreating ? '作成中...' : '新しいルームを作成'}
            </button>
          </div>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">または</span>
            </div>
          </div>

          <div>
            <label htmlFor="roomId" className="block text-sm font-medium text-gray-700 mb-2">
              ルームID
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                id="roomId"
                value={roomId}
                onChange={(e) => setRoomId(e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                placeholder="ルームIDを入力"
              />
              <button
                onClick={joinRoom}
                disabled={!roomId.trim() || !playerName.trim()}
                className="bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                参加
              </button>
            </div>
          </div>
        </div>

        <div className="mt-8 text-center text-sm text-gray-500">
          <p>感情を演技で表現し、みんなで推理するゲームです</p>
        </div>
      </div>
    </div>
  );
}