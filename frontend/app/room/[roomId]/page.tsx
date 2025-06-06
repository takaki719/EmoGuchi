'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { useSocket } from '@/hooks/useSocket';
import { useGameStore } from '@/stores/gameStore';

export default function RoomPage({ params }: { params: { roomId: string } }) {
  const searchParams = useSearchParams();
  const playerName = searchParams.get('name') || '';
  const isHost = searchParams.get('host') === 'true';
  
  const { roomId } = params;
  const { joinRoom, startRound, submitVote, leaveRoom, isConnected } = useSocket();
  const {
    roomState,
    currentRound,
    speakerEmotion,
    playerVote,
    lastResult,
    error,
    setPlayerName,
    setPlayerVote
  } = useGameStore();

  const [selectedEmotion, setSelectedEmotion] = useState('');
  const [copySuccess, setCopySuccess] = useState(false);
  const [isStartingRound, setIsStartingRound] = useState(false);

  useEffect(() => {
    if (playerName) {
      setPlayerName(playerName);
    }
  }, [playerName, setPlayerName]);

  useEffect(() => {
    if (isConnected && playerName && !roomState) {
      joinRoom(roomId, playerName);
    }
  }, [isConnected, playerName, roomId, roomState, joinRoom]);

  const handleStartRound = () => {
    if (isStartingRound) return; // Prevent double-click
    setIsStartingRound(true);
    startRound();
    // Reset after a delay to allow for server response
    setTimeout(() => setIsStartingRound(false), 2000);
  };

  const handleVote = () => {
    if (currentRound && selectedEmotion) {
      submitVote(currentRound.id, selectedEmotion);
      setPlayerVote(selectedEmotion);
      setSelectedEmotion('');
    }
  };

  const handleCopyRoomId = async () => {
    try {
      await navigator.clipboard.writeText(roomId);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (err) {
      console.error('Failed to copy room ID:', err);
    }
  };

  const handleLeaveRoom = () => {
    if (confirm('本当にルームから退出しますか？')) {
      leaveRoom();
      // Navigate back to home after leaving
      setTimeout(() => {
        window.location.href = '/';
      }, 1000);
    }
  };

  const emotionChoices = [
    { id: 'joy', name: '喜び' },
    { id: 'anger', name: '怒り' },
    { id: 'sadness', name: '悲しみ' },
    { id: 'surprise', name: '驚き' },
  ];

  const isCurrentSpeaker = currentRound?.speaker_name === playerName;

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md w-full text-center">
          <h2 className="text-red-800 font-bold mb-2">エラー</h2>
          <p className="text-red-600">{error}</p>
          <button
            onClick={() => window.location.href = '/'}
            className="mt-4 bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
          >
            ホームに戻る
          </button>
        </div>
      </div>
    );
  }

  if (!isConnected) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>サーバーに接続中...</p>
        </div>
      </div>
    );
  }

  if (!roomState) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>ルームに参加中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-800">🎭 EMOGUCHI</h1>
              <div className="flex items-center gap-2">
                <span className="text-gray-600">合言葉: {roomId}</span>
                <button
                  onClick={handleCopyRoomId}
                  className={`px-2 py-1 text-xs rounded transition-colors ${
                    copySuccess
                      ? 'bg-green-100 text-green-700'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                  title="合言葉をコピー"
                >
                  {copySuccess ? '✓ コピー済み' : '📋 コピー'}
                </button>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <button
                onClick={handleLeaveRoom}
                className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors"
                title="ルームから退出"
              >
                退出
              </button>
              <div className="text-right">
                <p className="text-sm text-gray-500">フェーズ</p>
                <p className="font-semibold">
                  {roomState.phase === 'waiting' && '待機中'}
                  {roomState.phase === 'in_round' && 'ラウンド中'}
                  {roomState.phase === 'result' && '結果発表'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Players */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">プレイヤー ({roomState.players.length}名)</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {roomState.players.map((player, index) => (
              <div
                key={player}
                className={`p-3 rounded-lg border-2 ${
                  player === playerName
                    ? 'border-blue-500 bg-blue-50'
                    : player === roomState.current_speaker
                    ? 'border-green-500 bg-green-50'
                    : 'border-gray-200 bg-gray-50'
                }`}
              >
                <div className="text-sm font-medium">{player}</div>
                {player === playerName && (
                  <div className="text-xs text-blue-600">あなた</div>
                )}
                {player === roomState.currentSpeaker && (
                  <div className="text-xs text-green-600">スピーカー</div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Game Area */}
        <div className="bg-white rounded-lg shadow-md p-6">
          {roomState.phase === 'waiting' && (
            <div className="text-center">
              <h2 className="text-xl font-semibold mb-4">ゲーム開始を待っています</h2>
              {isHost && (
                <button
                  onClick={handleStartRound}
                  disabled={roomState.players.length < 2 || isStartingRound}
                  className={`px-6 py-3 rounded-lg font-medium ${
                    roomState.players.length < 2 || isStartingRound
                      ? 'bg-gray-400 text-gray-600 cursor-not-allowed'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  {isStartingRound ? '開始中...' : roomState.players.length < 2 ? '2人以上必要' : 'ラウンド開始'}
                </button>
              )}
              {!isHost && (
                <p className="text-gray-600">ホストがゲームを開始するのを待っています...</p>
              )}
            </div>
          )}

          {roomState.phase === 'in_round' && (
            <div className="space-y-6">
              {currentRound ? (
                <>
                  <div className="text-center">
                    <h2 className="text-xl font-semibold mb-2">
                      スピーカー: {currentRound.speaker_name}
                    </h2>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-lg">{currentRound.phrase}</p>
                    </div>
                  </div>
                </>
              ) : (
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                  <p>ラウンドデータを読み込み中...</p>
                </div>
              )}

              {currentRound && isCurrentSpeaker && speakerEmotion && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <h3 className="font-semibold text-yellow-800 mb-2">あなたの演技する感情:</h3>
                  <p className="text-yellow-700">{speakerEmotion}</p>
                  <p className="text-sm text-yellow-600 mt-2">
                    この感情で上のセリフを読み上げてください
                  </p>
                </div>
              )}

              {currentRound && !isCurrentSpeaker && !playerVote && (
                <div className="space-y-4">
                  <h3 className="font-semibold">感情を推測してください:</h3>
                  <div className="grid grid-cols-2 gap-3">
                    {emotionChoices.map((emotion) => (
                      <button
                        key={emotion.id}
                        onClick={() => setSelectedEmotion(emotion.id)}
                        className={`p-3 rounded-lg border-2 transition-colors ${
                          selectedEmotion === emotion.id
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        {emotion.name}
                      </button>
                    ))}
                  </div>
                  <button
                    onClick={handleVote}
                    disabled={!selectedEmotion}
                    className="w-full bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 disabled:bg-gray-400 font-medium"
                  >
                    投票する
                  </button>
                </div>
              )}

              {currentRound && !isCurrentSpeaker && playerVote && (
                <div className="text-center bg-green-50 p-4 rounded-lg">
                  <p className="text-green-800">投票完了！</p>
                  <p className="text-green-600">他のプレイヤーを待っています...</p>
                </div>
              )}
            </div>
          )}

          {lastResult && (
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-center">結果発表</h2>
              <div className="bg-blue-50 p-4 rounded-lg">
                <p className="text-center mb-2">
                  <span className="font-semibold">正解:</span> {lastResult.correct_emotion}
                </p>
                <p className="text-center">
                  <span className="font-semibold">スピーカー:</span> {lastResult.speaker_name}
                </p>
              </div>
              
              <div>
                <h3 className="font-semibold mb-2">現在のスコア:</h3>
                <div className="space-y-2">
                  {Object.entries(lastResult.scores).map(([player, score]) => (
                    <div key={player} className="flex justify-between p-2 bg-gray-50 rounded">
                      <span>{player}</span>
                      <span className="font-semibold">{score}pt</span>
                    </div>
                  ))}
                </div>
              </div>

              {isHost && (
                <button
                  onClick={handleStartRound}
                  disabled={isStartingRound}
                  className={`w-full py-3 rounded-lg font-medium ${
                    isStartingRound
                      ? 'bg-gray-400 text-gray-600 cursor-not-allowed'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  {isStartingRound ? '開始中...' : '次のラウンド'}
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}