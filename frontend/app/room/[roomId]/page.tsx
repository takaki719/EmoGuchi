'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { useSocket } from '@/hooks/useSocket';
import { useGameStore } from '@/stores/gameStore';

export default function RoomPage({ params }: { params: { roomId: string } }) {
  const searchParams = useSearchParams();
  const playerName = searchParams.get('name') || '';
  const isHost = searchParams.get('host') === 'true';
  
  const { roomId: encodedRoomId } = params;
  const roomId = decodeURIComponent(encodedRoomId);
  const { joinRoom, startRound, submitVote, leaveRoom, restartGame, isConnected } = useSocket();
  const {
    roomState,
    currentRound,
    speakerEmotion,
    playerVote,
    lastResult,
    gameComplete,
    error,
    setPlayerName,
    setPlayerVote,
    setGameComplete,
    setLastResult
  } = useGameStore();

  const [selectedEmotion, setSelectedEmotion] = useState('');
  const [copySuccess, setCopySuccess] = useState(false);
  const [isStartingRound, setIsStartingRound] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [gameMode, setGameMode] = useState<'basic' | 'advanced'>('basic');
  const [maxRounds, setMaxRounds] = useState(3);
  const [speakerOrder, setSpeakerOrder] = useState<'sequential' | 'random'>('sequential');

  useEffect(() => {
    if (playerName) {
      setPlayerName(playerName);
    }
  }, [playerName, setPlayerName]);

  // Reset starting state when round actually starts or phase changes
  useEffect(() => {
    if (currentRound || roomState?.phase === 'in_round') {
      setIsStartingRound(false);
    }
  }, [currentRound, roomState?.phase]);

  useEffect(() => {
    if (isConnected && playerName && !roomState) {
      joinRoom(roomId, playerName);
    }
  }, [isConnected, playerName, roomId, roomState, joinRoom]);

  // Update local state when room state changes
  useEffect(() => {
    if (roomState?.config) {
      setGameMode(roomState.config.mode);
      setMaxRounds(roomState.config.max_rounds);
      setSpeakerOrder(roomState.config.speaker_order);
    }
  }, [roomState?.config]);

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
      // Fallback for browsers that don't support clipboard API
      alert(`合言葉: ${roomId}`);
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

  const handleUpdateSettings = async () => {
    try {
      const hostToken = localStorage.getItem('hostToken');
      if (!hostToken) {
        alert('ホスト権限がありません');
        return;
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002'}/api/v1/rooms/${encodeURIComponent(roomId)}/config`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${hostToken}`
        },
        body: JSON.stringify({
          mode: gameMode,
          vote_type: gameMode === 'advanced' ? '8choice' : '4choice',
          speaker_order: speakerOrder,
          max_rounds: maxRounds
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to update settings' }));
        throw new Error(errorData.detail || 'Failed to update settings');
      }

      setShowSettings(false);
      alert('設定を更新しました');
    } catch (error: any) {
      console.error('Error updating settings:', error);
      alert(`設定の更新に失敗しました: ${error.message}`);
    }
  };

  // Use dynamic voting choices from the current round, or fall back to static choices
  const emotionChoices = currentRound?.voting_choices && currentRound.voting_choices.length > 0 
    ? currentRound.voting_choices 
    : (() => {
        // Fallback static choices
        const basicChoices = [
          { id: 'joy', name: '喜び' },
          { id: 'anger', name: '怒り' },
          { id: 'sadness', name: '悲しみ' },
          { id: 'surprise', name: '驚き' },
        ];

        if (roomState?.config?.vote_type === '8choice') {
          return [
            ...basicChoices,
            { id: 'fear', name: '恐れ' },
            { id: 'disgust', name: '嫌悪' },
            { id: 'trust', name: '信頼' },
            { id: 'anticipation', name: '期待' },
          ];
        }

        return basicChoices;
      })();

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
                    : player === roomState.currentSpeaker
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
            <div className="space-y-6">
              <div className="text-center">
                <h2 className="text-xl font-semibold mb-4">ゲーム開始を待っています</h2>
                
                {/* Current Settings Display */}
                <div className="bg-gray-50 p-4 rounded-lg mb-4">
                  <h3 className="font-semibold mb-2">現在の設定</h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">感情モード:</span>
                      <span className="ml-2">{roomState.config.mode === 'basic' ? '基本感情 (4択)' : '応用感情 (8択)'}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">ラウンド数:</span>
                      <span className="ml-2">{roomState.config.max_rounds}周</span>
                    </div>
                    <div>
                      <span className="text-gray-600">発言順:</span>
                      <span className="ml-2">{roomState.config.speaker_order === 'sequential' ? '順番' : 'ランダム'}</span>
                    </div>
                  </div>
                </div>

                {isHost && (
                  <div className="space-y-3">
                    <button
                      onClick={() => setShowSettings(!showSettings)}
                      className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                    >
                      ⚙️ 設定変更
                    </button>
                    
                    {showSettings && (
                      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-left">
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
                        <div className="mb-4">
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

                        <div className="flex gap-2">
                          <button
                            onClick={handleUpdateSettings}
                            className="flex-1 bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition-colors"
                          >
                            設定を保存
                          </button>
                          <button
                            onClick={() => setShowSettings(false)}
                            className="flex-1 bg-gray-400 text-white py-2 px-4 rounded-lg hover:bg-gray-500 transition-colors"
                          >
                            キャンセル
                          </button>
                        </div>
                      </div>
                    )}
                    
                    <button
                      onClick={handleStartRound}
                      disabled={roomState.players.length < 2 || isStartingRound}
                      className={`px-6 py-3 rounded-lg font-medium ${
                        roomState.players.length < 2 || isStartingRound
                          ? 'bg-gray-400 text-gray-600 cursor-not-allowed'
                          : 'bg-green-600 text-white hover:bg-green-700'
                      }`}
                    >
                      {isStartingRound ? '開始中...' : roomState.players.length < 2 ? '2人以上必要' : '🎮 ゲーム開始'}
                    </button>
                  </div>
                )}
                
                {!isHost && (
                  <p className="text-gray-600">ホストがゲームを開始するのを待っています...</p>
                )}
              </div>
            </div>
          )}

          {roomState.phase === 'in_round' && (
            <div className="space-y-6">
              {currentRound ? (
                <>
                  {!isCurrentSpeaker ? (
                    // リスナー向けの表示
                    <div className="text-center">
                      <h2 className="text-xl font-semibold mb-2">
                        スピーカー: {currentRound.speaker_name}
                      </h2>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <p className="text-lg">{currentRound.phrase}</p>
                      </div>
                      <p className="text-sm text-gray-600 mt-2">
                        スピーカーが演技するのを聞いて、感情を推測してください
                      </p>
                    </div>
                  ) : (
                    // スピーカー向けの表示
                    <div className="text-center">
                      <h2 className="text-xl font-semibold mb-4 text-orange-700">
                        🎭 あなたがスピーカーです
                      </h2>
                      <div className="bg-orange-50 border-2 border-orange-200 rounded-lg p-6">
                        <h3 className="font-bold text-orange-800 mb-3 text-lg">演技してください:</h3>
                        <div className="space-y-4">
                          <div>
                            <h4 className="font-semibold text-orange-700 mb-1">セリフ:</h4>
                            <p className="text-xl font-medium text-orange-900 bg-white p-3 rounded border">{currentRound.phrase}</p>
                          </div>
                          {speakerEmotion && (
                            <div>
                              <h4 className="font-semibold text-orange-700 mb-1">感情:</h4>
                              <p className="text-lg font-medium text-orange-900 bg-white p-3 rounded border">{speakerEmotion}</p>
                            </div>
                          )}
                        </div>
                        <p className="text-sm text-orange-700 mt-4 font-medium">
                          この感情でセリフを読み上げてください。他の参加者があなたの感情を推測します。
                        </p>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                  <p>ラウンドデータを読み込み中...</p>
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
                <div className="text-center space-y-3">
                  <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                    <p className="text-blue-800 font-semibold mb-2">投票完了！</p>
                    <div className="text-sm">
                      <span className="text-blue-600">あなたの投票: </span>
                      <span className="font-medium text-blue-800">
                        {emotionChoices.find(e => e.id === playerVote)?.name || playerVote}
                      </span>
                    </div>
                  </div>
                  <p className="text-gray-600 text-sm">他のプレイヤーを待っています...</p>
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

              {/* Player's Vote Result */}
              {lastResult.votes && lastResult.votes[playerName] && (
                <div className={`p-4 rounded-lg border-2 ${
                  (() => {
                    const playerVotedEmotion = lastResult.votes[playerName];
                    const correctEmotionId = lastResult.correctEmotionId;
                    const isCorrect = correctEmotionId ? playerVotedEmotion === correctEmotionId : false;
                    return isCorrect ? 'border-green-400 bg-green-50' : 'border-red-400 bg-red-50';
                  })()
                }`}>
                  <div className="text-center">
                    <p className="font-semibold mb-1">
                      {(() => {
                        const playerVotedEmotion = lastResult.votes[playerName];
                        const correctEmotionId = lastResult.correctEmotionId;
                        const isCorrect = correctEmotionId ? playerVotedEmotion === correctEmotionId : false;
                        return isCorrect ? '🎉 正解！' : '❌ 不正解';
                      })()}
                    </p>
                    <p className="text-sm">
                      <span className="text-gray-600">あなたの投票: </span>
                      <span className="font-medium">
                        {emotionChoices.find(e => e.id === lastResult.votes[playerName])?.name || lastResult.votes[playerName]}
                      </span>
                    </p>
                    {(() => {
                      const playerVotedEmotion = lastResult.votes[playerName];
                      const correctEmotionId = lastResult.correctEmotionId;
                      const isCorrect = correctEmotionId ? playerVotedEmotion === correctEmotionId : false;
                      if (isCorrect) {
                        return <p className="text-green-700 text-sm mt-1">+1ポイント獲得！</p>;
                      } else {
                        return <p className="text-red-700 text-sm mt-1">今回はポイントなし</p>;
                      }
                    })()}
                  </div>
                </div>
              )}
              
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

              {isHost && !lastResult.isGameComplete && (
                <div className="space-y-2">
                  <div className="text-center text-sm text-gray-600 mb-2">
                    ラウンド {(lastResult.completedRounds || 0) + 1}/{lastResult.maxRounds || roomState?.config?.max_rounds || 3}
                  </div>
                  <button
                    onClick={handleStartRound}
                    disabled={isStartingRound}
                    className={`w-full py-3 rounded-lg font-medium ${
                      isStartingRound
                        ? 'bg-gray-400 text-gray-600 cursor-not-allowed'
                        : 'bg-blue-600 text-white hover:bg-blue-700'
                    }`}
                  >
                    {isStartingRound ? '準備中...' : '➡️ 次のラウンドへ'}
                  </button>
                </div>
              )}

              {lastResult.isGameComplete && (
                <div className="text-center bg-yellow-50 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold text-yellow-800 mb-2">
                    🎉 ゲーム終了！
                  </h3>
                  <p className="text-yellow-700">
                    {lastResult.completedRounds}/{lastResult.maxRounds}ラウンド完了
                  </p>
                </div>
              )}
            </div>
          )}

          {gameComplete && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-center text-gold">🏆 最終結果発表</h2>
              
              <div className="bg-gradient-to-br from-yellow-50 to-orange-50 p-6 rounded-lg border-2 border-yellow-200">
                <h3 className="text-xl font-semibold mb-4 text-center">順位表</h3>
                <div className="space-y-3">
                  {gameComplete.rankings.map((player, index) => (
                    <div key={player.name} className={`flex items-center justify-between p-4 rounded-lg ${
                      index === 0 ? 'bg-yellow-100 border-2 border-yellow-400' :
                      index === 1 ? 'bg-gray-100 border-2 border-gray-400' :
                      index === 2 ? 'bg-orange-100 border-2 border-orange-400' :
                      'bg-white border border-gray-200'
                    }`}>
                      <div className="flex items-center gap-3">
                        <span className={`text-2xl font-bold ${
                          index === 0 ? 'text-yellow-600' :
                          index === 1 ? 'text-gray-600' :
                          index === 2 ? 'text-orange-600' :
                          'text-gray-500'
                        }`}>
                          {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `${player.rank}位`}
                        </span>
                        <span className={`font-semibold ${
                          player.name === playerName ? 'text-blue-600' : 'text-gray-800'
                        }`}>
                          {player.name}
                          {player.name === playerName && ' (あなた)'}
                        </span>
                      </div>
                      <span className="text-xl font-bold text-gray-800">{player.score}pt</span>
                    </div>
                  ))}
                </div>
                
                <div className="mt-6 text-center text-gray-600">
                  <p>全{gameComplete.totalRounds}ラウンドお疲れ様でした！</p>
                </div>
              </div>

              {isHost && (
                <div className="space-y-4">
                  {/* Settings Section for Next Game */}
                  <div className="bg-white p-4 rounded-lg border border-gray-200">
                    <h4 className="font-semibold mb-3 text-center">次のゲーム設定</h4>
                    
                    {/* Current Settings Display */}
                    <div className="bg-gray-50 p-3 rounded-lg mb-3">
                      <h5 className="font-medium mb-2 text-sm">現在の設定</h5>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>
                          <span className="text-gray-600">感情モード:</span>
                          <span className="ml-1">{roomState?.config.mode === 'basic' ? '基本 (4択)' : '応用 (8択)'}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">ラウンド数:</span>
                          <span className="ml-1">{roomState?.config.max_rounds}周</span>
                        </div>
                        <div className="col-span-2">
                          <span className="text-gray-600">発言順:</span>
                          <span className="ml-1">{roomState?.config.speaker_order === 'sequential' ? '順番' : 'ランダム'}</span>
                        </div>
                      </div>
                    </div>
                    
                    <button
                      onClick={() => setShowSettings(!showSettings)}
                      className="w-full px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm"
                    >
                      ⚙️ 設定変更
                    </button>
                    
                    {showSettings && (
                      <div className="mt-3 p-3 border border-gray-200 rounded-lg bg-gray-50">
                        {/* Game Mode */}
                        <div className="mb-3">
                          <label className="block text-xs font-medium text-gray-700 mb-1">
                            感情モード
                          </label>
                          <div className="grid grid-cols-2 gap-1">
                            <button
                              type="button"
                              onClick={() => setGameMode('basic')}
                              className={`px-2 py-1 rounded text-xs font-medium transition-all ${
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
                              className={`px-2 py-1 rounded text-xs font-medium transition-all ${
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
                        <div className="mb-3">
                          <label htmlFor="maxRounds" className="block text-xs font-medium text-gray-700 mb-1">
                            ラウンド数
                          </label>
                          <select
                            id="maxRounds"
                            value={maxRounds}
                            onChange={(e) => setMaxRounds(Number(e.target.value))}
                            className="w-full px-2 py-1 border border-gray-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-transparent"
                          >
                            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(num => (
                              <option key={num} value={num}>{num}周</option>
                            ))}
                          </select>
                        </div>

                        {/* Speaker Order */}
                        <div className="mb-3">
                          <label className="block text-xs font-medium text-gray-700 mb-1">
                            発言順
                          </label>
                          <div className="grid grid-cols-2 gap-1">
                            <button
                              type="button"
                              onClick={() => setSpeakerOrder('sequential')}
                              className={`px-2 py-1 rounded text-xs font-medium transition-all ${
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
                              className={`px-2 py-1 rounded text-xs font-medium transition-all ${
                                speakerOrder === 'random'
                                  ? 'bg-blue-600 text-white'
                                  : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                              }`}
                            >
                              ランダム
                            </button>
                          </div>
                        </div>

                        <div className="flex gap-1">
                          <button
                            onClick={handleUpdateSettings}
                            className="flex-1 bg-green-600 text-white py-1 px-2 rounded text-xs hover:bg-green-700 transition-colors"
                          >
                            設定を保存
                          </button>
                          <button
                            onClick={() => setShowSettings(false)}
                            className="flex-1 bg-gray-400 text-white py-1 px-2 rounded text-xs hover:bg-gray-500 transition-colors"
                          >
                            キャンセル
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <button
                    onClick={() => {
                      setGameComplete(null);
                      setLastResult(null);
                      restartGame();
                    }}
                    className="w-full bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 font-medium"
                  >
                    🔄 もう一度プレイ
                  </button>
                  <p className="text-center text-sm text-gray-500">
                    スコアをリセットして新しいゲームを開始します
                  </p>
                </div>
              )}

              {!isHost && (
                <div className="text-center text-gray-600">
                  <p>ホストが次のゲームを開始するのを待っています...</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}