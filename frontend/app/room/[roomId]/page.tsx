'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { useSocket } from '@/hooks/useSocket';
import { useGameStore } from '@/stores/gameStore';
import { useLocaleStore } from '@/stores/localeStore';
import { translations } from '@/lib/translations';
import { AudioRecorder } from '@/components/AudioRecorder';
import { AudioPlayer } from '@/components/AudioPlayer';
import EmotionWheel3Layer from '@/components/EmotionWheel3Layer';
import VoteTimer from '@/components/VoteTimer';
import { getApiUrl } from '@/utils/api';

// Edge Runtime 対応
export const runtime = 'edge';

export default function RoomPage({ params }: { params: { roomId: string } }) {
  const searchParams = useSearchParams();
  const playerName = searchParams.get('name') || '';
  const isHost = searchParams.get('host') === 'true';
  
  const { roomId: encodedRoomId } = params;
  const roomId = decodeURIComponent(encodedRoomId);
  const { joinRoom, startRound, submitVote, leaveRoom, restartGame, sendAudio, isConnected } = useSocket();
  const {
    roomState,
    currentRound,
    speakerEmotion,
    playerVote,
    lastResult,
    gameComplete,
    error,
    audioUrl,
    isAudioProcessed,
    voteTimer,
    setPlayerName,
    setPlayerVote,
    setGameComplete,
    setLastResult,
    setAudioRecording,
    setAudioUrl,
    setError
  } = useGameStore();

  const [selectedEmotion, setSelectedEmotion] = useState('');
  const [copySuccess, setCopySuccess] = useState(false);
  const [isStartingRound, setIsStartingRound] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [gameMode, setGameMode] = useState<'basic' | 'advanced' | 'wheel'>('basic');
  const [maxRounds, setMaxRounds] = useState(1);
  const [speakerOrder, setSpeakerOrder] = useState<'sequential' | 'random'>('sequential');
  const [hardMode, setHardMode] = useState(false);
  const { locale } = useLocaleStore();
  const t = translations[locale];

  // Helper function to translate emotion ID to localized name using i18n
  const getEmotionDisplayName = (emotion: string): string => {
    if (!emotion) return '';
    
    // Check if it's already a localized emotion name
    const currentEmotions = Object.values(t.emotions) as string[];
    if (currentEmotions.includes(emotion)) {
      return emotion;
    }
    
    // Map emotion ID to localized name using i18n
    const emotionKey = emotion as keyof typeof t.emotions;
    if (emotionKey in t.emotions) {
      return t.emotions[emotionKey];
    }
    
    return emotion; // fallback to original if not found
  };

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
      console.log('🔧 Updating settings from roomState:', roomState.config);
      setGameMode(roomState.config.mode);
      setMaxRounds(roomState.config.max_rounds);
      setSpeakerOrder(roomState.config.speaker_order);
      setHardMode(roomState.config.hard_mode || false);
      console.log('🔧 Settings updated - maxRounds set to:', roomState.config.max_rounds);
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
      alert(`${t.common.roomId}: ${roomId}`);
    }
  };

  const handleLeaveRoom = () => {
    if (confirm(t.common.leaveRoomConfirm)) {
      leaveRoom();
      // Navigate back to home after leaving
      setTimeout(() => {
        window.location.href = '/';
      }, 1000);
    }
  };

  const handleAudioRecording = (audioBlob: Blob) => {
    console.log('🎤 handleAudioRecording called with blob:', audioBlob);
    console.log('Blob size:', audioBlob.size, 'type:', audioBlob.type);
    
    // Validate audio blob
    if (!audioBlob || audioBlob.size === 0) {
      console.error('❌ Invalid audio blob received');
      setError('録音データが無効です. 再試行してください.');
      return;
    }
    
    // Check blob size (should be reasonable)
    if (audioBlob.size < 1000) { // Less than 1KB might be too small
      console.warn('⚠️ Audio blob seems very small:', audioBlob.size, 'bytes');
    }
    
    if (audioBlob.size > 50 * 1024 * 1024) { // More than 50MB might be too large
      console.warn('⚠️ Audio blob seems very large:', audioBlob.size, 'bytes');
      setError('録音データが大きすぎます. 短めの録音をお試しください.');
      return;
    }
    
    try {
      setAudioRecording(audioBlob);
      sendAudio(audioBlob);
      console.log('📤 Audio sent to server via sendAudio function');
    } catch (error) {
      console.error('❌ Error sending audio:', error);
      setError('音声送信でエラーが発生しました. 再試行してください.');
    }
  };

  // Helper function to get emotion name by ID for wheel mode
  const getEmotionNameById = (emotionId: string): string => {
    if (roomState?.config?.vote_type === 'wheel') {
      // For wheel mode, import emotions from EmotionWheel3Layer
      const { PLUTCHIK_EMOTIONS_3_LAYER } = require('@/components/EmotionWheel3Layer');
      const emotion = PLUTCHIK_EMOTIONS_3_LAYER.find((e: any) => e.id === emotionId);
      if (emotion) {
        // For wheel mode, show both localized names based on current language
        if (locale === 'ja') {
          return emotion.nameJa;
        } else {
          return emotion.nameEn;
        }
      }
    } else {
      // For choice modes, use emotionChoices
      const emotion = emotionChoices.find(e => e.id === emotionId);
      if (emotion) {
        return emotion.name;
      }
      
      // Fallback: try to translate using getEmotionDisplayName
      return getEmotionDisplayName(emotionId);
    }
    return emotionId; // fallback
  };

  const handleUpdateSettings = async () => {
    console.log('🔐 handleUpdateSettings called');
    try {
      const hostToken = localStorage.getItem('hostToken');
      console.log('🔐 Host token from localStorage:', hostToken ? `${hostToken.substring(0, 8)}...` : 'null');
      if (!hostToken) {
        alert(t.common.noHostPrivileges);
        return;
      }

      const requestBody = {
        mode: gameMode,
        vote_type: gameMode === 'advanced' ? '8choice' : 
                  gameMode === 'wheel' ? 'wheel' : '4choice',
        speaker_order: speakerOrder,
        max_rounds: maxRounds,
        hard_mode: hardMode
      };
      
      const url = `${getApiUrl()}/api/v1/rooms/${encodeURIComponent(roomId)}/config`;
      console.log('🔐 Settings update URL:', url);
      console.log('🔐 Current state values - maxRounds:', maxRounds, 'gameMode:', gameMode);
      console.log('🔐 Settings update body:', requestBody);
      
      const response = await fetch(url, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${hostToken}`
        },
        body: JSON.stringify(requestBody),
      });

      console.log('🔐 Settings update response status:', response.status);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to update settings' }));
        console.log('🔐 Settings update error:', errorData);
        throw new Error(errorData.detail || 'Failed to update settings');
      }

      setShowSettings(false);
      alert(t.common.settingsUpdated);
    } catch (error: any) {
      console.error('Error updating settings:', error);
      alert(`${t.common.settingsUpdateFailed}: ${error.message}`);
    }
  };

  // Use dynamic voting choices from the current round, or fall back to static choices
  const emotionChoices = currentRound?.voting_choices && currentRound.voting_choices.length > 0 
    ? currentRound.voting_choices 
    : (() => {
        // Fallback static choices
        const basicChoices = [
          { id: 'joy', name: t.emotions.joy },
          { id: 'anger', name: t.emotions.anger },
          { id: 'sadness', name: t.emotions.sadness },
          { id: 'surprise', name: t.emotions.surprise },
        ];

        if (roomState?.config?.vote_type === '8choice') {
          return [
            ...basicChoices,
            { id: 'fear', name: t.emotions.fear },
            { id: 'disgust', name: t.emotions.disgust },
            { id: 'trust', name: t.emotions.trust },
            { id: 'anticipation', name: t.emotions.anticipation },
          ];
        }

        return basicChoices;
      })();

  const isCurrentSpeaker = currentRound?.speaker_name === playerName;

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md w-full text-center">
          <h2 className="text-red-800 font-bold mb-2">{t.common.error}</h2>
          <p className="text-red-600">{error}</p>
          <button
            onClick={() => window.location.href = '/'}
            className="mt-4 bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
          >
            {t.common.backToHome}
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
          <p>{t.common.connecting}</p>
        </div>
      </div>
    );
  }

  if (!roomState) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>{t.common.joiningRoom}</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="min-h-screen p-2 sm:p-4">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="bg-white rounded-lg shadow-md p-3 sm:p-6 mb-4 sm:mb-6">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 sm:gap-0">
            <div className="w-full sm:w-auto">
              <h1 className="text-xl sm:text-2xl font-bold text-gray-800">🎭 EMOGUCHI</h1>
              <div className="flex flex-col sm:flex-row sm:items-center gap-2 mt-1">
                <span className="text-sm sm:text-base text-gray-600">{t.common.roomId}: {roomId}</span>
                <button
                  onClick={handleCopyRoomId}
                  className={`px-3 py-2 sm:px-2 sm:py-1 text-sm sm:text-xs rounded transition-colors self-start ${
                    copySuccess
                      ? 'bg-green-100 text-green-700'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                  title={t.common.copyRoomCode}
                >
                  {copySuccess ? '✓' : '📋'}
                </button>
              </div>
            </div>
            <div className="flex items-center gap-3 sm:gap-4 w-full sm:w-auto justify-between sm:justify-end">
              <div className="text-left sm:text-right">
                <p className="text-xs sm:text-sm text-gray-500">{t.common.phase}</p>
                <p className="font-semibold text-sm sm:text-base">
                  {roomState.phase === 'waiting' && t.common.waiting}
                  {roomState.phase === 'in_round' && t.common.inRound}
                  {roomState.phase === 'result' && t.common.result}
                </p>
              </div>
              <button
                onClick={handleLeaveRoom}
                className="px-3 py-2 sm:px-3 sm:py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors"
                title={t.common.exit}
              >
                {t.common.exit}
              </button>
            </div>
          </div>
        </div>

        {/* Players */}
        <div className="bg-white rounded-lg shadow-md p-3 sm:p-6 mb-4 sm:mb-6">
          <h2 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4">{t.common.players} ({roomState.players.length}{t.game.peopleCounter})</h2>
          <div className={`grid gap-2 sm:gap-3 ${
            roomState.players.length <= 4 ? 'grid-cols-2 sm:grid-cols-4' :
            roomState.players.length <= 6 ? 'grid-cols-2 sm:grid-cols-3' :
            'grid-cols-2 sm:grid-cols-3 lg:grid-cols-4'
          }`}>
            {roomState.players.map((player, index) => (
              <div
                key={typeof player === 'string' ? player : player.name}
                className={`p-2 sm:p-3 rounded-lg border-2 ${
                  (typeof player === 'string' ? player : player.name) === playerName
                    ? 'border-blue-500 bg-blue-50'
                    : (typeof player === 'string' ? player : player.name) === roomState.currentSpeaker
                    ? 'border-green-500 bg-green-50'
                    : 'border-gray-200 bg-gray-50'
                }`}
              >
                <div className="text-xs sm:text-sm font-medium truncate" title={typeof player === 'string' ? player : player.name}>
                  {typeof player === 'string' ? player : player.name}
                </div>
                {typeof player === 'object' && player.score !== undefined && (
                  <div className="text-xs sm:text-sm font-bold text-gray-700">
                    {player.score}pt
                  </div>
                )}
                {(typeof player === 'string' ? player : player.name) === playerName && (
                  <div className="text-xs text-blue-600">{t.common.you}</div>
                )}
                {(typeof player === 'string' ? player : player.name) === roomState.currentSpeaker && (
                  <div className="text-xs text-green-600">{t.common.speaker}</div>
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
                <h2 className="text-xl font-semibold mb-4">{t.game.waitingForHost}</h2>
                
                {/* Current Settings Display - Hidden during active game */}
                {!lastResult && !gameComplete && (
                  <div className="bg-gray-50 p-4 rounded-lg mb-4">
                    <h3 className="font-semibold mb-2">{t.game.currentSettings}</h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">{t.home.gameMode}:</span>
                        <span className="ml-2">
                          {roomState.config.mode === 'basic' ? t.home.basicMode : 
                           roomState.config.mode === 'advanced' ? t.home.advancedMode : t.home.wheelMode}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-600">{t.home.maxCycles}:</span>
                        <span className="ml-2">{roomState.config.max_rounds}{t.home.cycle}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">{t.home.speakerOrder}:</span>
                        <span className="ml-2">{roomState.config.speaker_order === 'sequential' ? t.home.sequential : t.home.random}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">{t.home.hardMode}:</span>
                        <span className="ml-2">{roomState.config.hard_mode ? t.home.hardModeOn : t.home.hardModeOff}</span>
                      </div>
                    </div>
                  </div>
                )}

                {isHost && (
                  <div className="space-y-3">
                    {/* ゲーム開始前のみ設定変更ボタンを表示 */}
                    {roomState.phase === 'waiting' && !lastResult && (
                      <button
                        onClick={() => setShowSettings(!showSettings)}
                        className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                      >
                        ⚙️ {t.common.settings}
                      </button>
                    )}
                    
                    {showSettings && (
                      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-left">
                        {/* Game Mode */}
                        <div className="mb-4">
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            {t.home.gameMode}
                          </label>
                          <div className="grid grid-cols-3 gap-2">
                            <button
                              type="button"
                              onClick={() => setGameMode('basic')}
                              className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                                gameMode === 'basic'
                                  ? 'bg-blue-600 text-white'
                                  : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                              }`}
                            >
                              {t.home.basicMode}
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
                              {t.home.advancedMode}
                            </button>
                            <button
                              type="button"
                              onClick={() => setGameMode('wheel')}
                              className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                                gameMode === 'wheel'
                                  ? 'bg-blue-600 text-white'
                                  : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                              }`}
                            >
                              {t.home.wheelMode}
                            </button>
                          </div>
                        </div>

                        {/* Max Rounds */}
                        <div className="mb-4">
                          <label htmlFor="maxRounds" className="block text-sm font-medium text-gray-700 mb-2">
                            {t.home.maxCycles}
                          </label>
                          <select
                            id="maxRounds"
                            value={maxRounds}
                            onChange={(e) => setMaxRounds(Number(e.target.value))}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          >
                            {[1, 2, 3, 4, 5].map(num => (
                              <option key={num} value={num}>{num}{t.home.cycle}</option>
                            ))}
                          </select>
                        </div>

                        {/* Speaker Order */}
                        <div className="mb-4">
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            {t.home.speakerOrder}
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
                              {t.home.sequential}
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
                              {t.home.random}
                            </button>
                          </div>
                        </div>

                        {/* Hard Mode */}
                        <div className="mb-4">
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            {t.home.hardMode}
                          </label>
                          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-3">
                            <p className="text-xs text-yellow-800 mb-1">
                              🎯 音声加工でリスナーの感情判定を困難にします
                            </p>
                            <p className="text-xs text-yellow-700">
                              • ピッチ・テンポ変更による印象操作<br/>
                              • 感情逆転変換による誤誘導<br/>
                              • スピーカーには原音、リスナーには加工音声
                            </p>
                          </div>
                          <div className="grid grid-cols-2 gap-2">
                            <button
                              type="button"
                              onClick={() => setHardMode(false)}
                              className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                                !hardMode
                                  ? 'bg-blue-600 text-white'
                                  : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                              }`}
                            >
                              {t.home.hardModeOff}
                            </button>
                            <button
                              type="button"
                              onClick={() => setHardMode(true)}
                              className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                                hardMode
                                  ? 'bg-red-600 text-white'
                                  : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                              }`}
                            >
                              {t.home.hardModeOn}
                            </button>
                          </div>
                        </div>

                        <div className="flex gap-2">
                          <button
                            onClick={handleUpdateSettings}
                            className="flex-1 bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition-colors"
                          >
                            {t.common.save}
                          </button>
                          <button
                            onClick={() => setShowSettings(false)}
                            className="flex-1 bg-gray-400 text-white py-2 px-4 rounded-lg hover:bg-gray-500 transition-colors"
                          >
                            {t.common.cancel}
                          </button>
                        </div>
                      </div>
                    )}
                    
                    {/* ゲーム開始前のみゲーム開始ボタンを表示 */}
                    {roomState.phase === 'waiting' && !lastResult && (
                      <button
                        onClick={handleStartRound}
                        disabled={roomState.players.length < 2 || isStartingRound || showSettings}
                        className={`px-6 py-3 rounded-lg font-medium ${
                          roomState.players.length < 2 || isStartingRound || showSettings
                            ? 'bg-gray-400 text-gray-600 cursor-not-allowed'
                            : 'bg-green-600 text-white hover:bg-green-700'
                        }`}
                      >
                        {isStartingRound ? t.game.starting : 
                         showSettings ? '設定変更中...' :
                         roomState.players.length < 2 ? t.game.minimumPlayers : 
                         `🎮 ${t.game.gameStart}`}
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {roomState.phase === 'in_round' && (
            <div className="space-y-6">
              {currentRound && (
                <>
                  {!isCurrentSpeaker ? (
                    // リスナー向けの表示
                    <div className="text-center">
                      <h2 className="text-xl font-semibold mb-2">
                        {t.game.speakerIs} {currentRound.speaker_name}
                      </h2>
                      {roomState?.config?.hard_mode && (
                        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-3">
                          <p className="text-sm text-red-700">
                            🎯 <strong>高難易度モード</strong>：音声が加工されています
                          </p>
                          <p className="text-xs text-red-600 mt-1">
                            ピッチ・テンポ変更や感情逆転により判定が困難になっています
                          </p>
                        </div>
                      )}
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <p className="text-lg">{currentRound.phrase}</p>
                      </div>
                      <div className="mt-4">
                        {audioUrl ? (
                          <AudioPlayer 
                            audioUrl={audioUrl} 
                            speakerName={currentRound.speaker_name}
                            isProcessed={isAudioProcessed}
                          />
                        ) : (
                          <div className="bg-gray-100 p-4 rounded-lg border-2 border-gray-300">
                            <p className="text-gray-600 text-center">
                              📢 スピーカーの音声を待っています...
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    // スピーカー向けの表示
                    <div className="text-center">
                      <h2 className="text-xl font-semibold mb-4 text-orange-700">
                        {t.game.youAreSpeakerTitle}
                      </h2>
                      <div className="bg-orange-50 border-2 border-orange-200 rounded-lg p-6">
                        <h3 className="font-bold text-orange-800 mb-3 text-lg">{t.game.performWith}</h3>
                        <div className="space-y-4">
                          <div>
                            <h4 className="font-semibold text-orange-700 mb-1">{t.game.script}</h4>
                            <p className="text-xl font-medium text-orange-900 bg-white p-3 rounded border">{currentRound.phrase}</p>
                          </div>
                          
                          {/* Show assigned emotion for all modes */}
                          {speakerEmotion && (
                            <div>
                              <h4 className="font-semibold text-orange-700 mb-1">{t.game.emotion}</h4>
                              <p className="text-lg font-medium text-orange-900 bg-white p-3 rounded border">
                                {getEmotionDisplayName(speakerEmotion)}
                              </p>
                            </div>
                          )}
                        </div>
                        <p className="text-sm text-orange-700 mt-4 font-medium">
                          {t.game.speakerInstructions}
                        </p>
                        {roomState?.config?.hard_mode && (
                          <div className="bg-red-50 border border-red-200 rounded-lg p-3 mt-3">
                            <p className="text-sm text-red-700">
                              🎯 <strong>高難易度モード</strong>：あなたの音声はリスナーに加工されて届きます
                            </p>
                            <p className="text-xs text-red-600 mt-1">
                              あなたには原音が聞こえますが、リスナーには加工音声が再生されます
                            </p>
                          </div>
                        )}
                      </div>
                      <div className="mt-6">
                        <AudioRecorder 
                          onRecordingComplete={handleAudioRecording}
                          disabled={false}
                        />
                        {!speakerEmotion && (
                          <p className="text-sm text-orange-600 mt-2">
                            ⚠️ 感情情報を受信中... (録音は有効です)
                          </p>
                        )}
                      </div>
                    </div>
                  )}
                </>
              )}

              {currentRound && !isCurrentSpeaker && !playerVote && !audioUrl && (
                <div className="text-center bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <p className="text-yellow-700 font-medium">
                    ⏳ スピーカーの音声録音を待っています...
                  </p>
                  <p className="text-yellow-600 text-sm mt-1">
                    音声を聞いてから感情を選択してください
                  </p>
                </div>
              )}

              {currentRound && !isCurrentSpeaker && !playerVote && audioUrl && (
                <div className="space-y-3 sm:space-y-4">
                  {/* Vote Timer */}
                  {voteTimer.isActive && voteTimer.startTime && (
                    <VoteTimer
                      startTime={voteTimer.startTime}
                      timeoutSeconds={voteTimer.timeoutSeconds}
                      onTimeout={() => {
                        console.log('⏰ Vote timer expired on client side');
                        // サーバー側で自動的にラウンドが完了されるので、ここでは通知のみ
                      }}
                    />
                  )}
                  <h3 className="font-semibold text-sm sm:text-base">{t.game.guessEmotion}</h3>
                  {roomState?.config?.vote_type === 'wheel' ? (
                    <div className="flex flex-col items-center space-y-6">
                      <EmotionWheel3Layer
                        selectedEmotion={selectedEmotion}
                        onEmotionSelect={setSelectedEmotion}
                        size={400}
                      />
                      <button
                        onClick={handleVote}
                        disabled={!selectedEmotion}
                        className="w-full max-w-md bg-green-600 text-white py-3 sm:py-4 rounded-lg hover:bg-green-700 disabled:bg-gray-400 font-medium text-sm sm:text-base"
                      >
                        {t.game.vote}
                      </button>
                    </div>
                  ) : (
                    <>
                      <div className={`grid gap-2 sm:gap-3 ${
                        emotionChoices.length <= 4 ? 'grid-cols-2' : 'grid-cols-2 sm:grid-cols-4'
                      }`}>
                        {emotionChoices.map((emotion) => (
                          <button
                            key={emotion.id}
                            onClick={() => setSelectedEmotion(emotion.id)}
                            className={`p-3 sm:p-4 rounded-lg border-2 transition-colors text-sm sm:text-base ${
                              selectedEmotion === emotion.id
                                ? 'border-blue-500 bg-blue-50 font-semibold'
                                : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                            }`}
                          >
                            {emotion.name}
                          </button>
                        ))}
                      </div>
                      <button
                        onClick={handleVote}
                        disabled={!selectedEmotion}
                        className="w-full bg-green-600 text-white py-3 sm:py-4 rounded-lg hover:bg-green-700 disabled:bg-gray-400 font-medium text-sm sm:text-base"
                      >
                        {t.game.vote}
                      </button>
                    </>
                  )}
                </div>
              )}

              {currentRound && !isCurrentSpeaker && playerVote && (
                <div className="text-center space-y-3">
                  {/* Vote Timer for voters who have already voted */}
                  {voteTimer.isActive && voteTimer.startTime && (
                    <VoteTimer
                      startTime={voteTimer.startTime}
                      timeoutSeconds={voteTimer.timeoutSeconds}
                      onTimeout={() => {
                        console.log('⏰ Vote timer expired on client side');
                        // サーバー側で自動的にラウンドが完了されるので、ここでは通知のみ
                      }}
                    />
                  )}
                  <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                    <p className="text-blue-800 font-semibold mb-2">{t.game.voteComplete}</p>
                    <div className="text-sm">
                      <span className="text-blue-600">{t.game.yourVote}: </span>
                      <span className="font-medium text-blue-800">
                        {getEmotionNameById(playerVote)}
                      </span>
                    </div>
                  </div>
                  <p className="text-gray-600 text-sm">{t.game.waitingForOthers}</p>
                </div>
              )}
            </div>
          )}

          {lastResult && (
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-center">{t.game.resultAnnouncement}</h2>
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
                    <p className={`text-xl font-bold mb-2 ${
                      (() => {
                        const playerVotedEmotion = lastResult.votes[playerName];
                        const correctEmotionId = lastResult.correctEmotionId;
                        const isCorrect = correctEmotionId ? playerVotedEmotion === correctEmotionId : false;
                        return isCorrect ? 'text-green-700' : 'text-red-700';
                      })()
                    }`}>
                      {(() => {
                        const playerVotedEmotion = lastResult.votes[playerName];
                        const correctEmotionId = lastResult.correctEmotionId;
                        const isCorrect = correctEmotionId ? playerVotedEmotion === correctEmotionId : false;
                        return isCorrect ? t.game.correctEmoji : t.game.incorrectEmoji;
                      })()}
                    </p>
                    <div className="space-y-2">
                      <p className="text-sm">
                        <span className="text-gray-600">{t.game.yourVoteLabel} </span>
                        <span className="font-medium">
                          {getEmotionNameById(lastResult.votes[playerName])}
                        </span>
                      </p>
                      <p className="text-sm">
                        <span className="text-gray-600">{t.game.correctAnswerLabel} </span>
                        <span className="font-medium">
                          {getEmotionNameById(lastResult.correctEmotionId || '')}
                        </span>
                      </p>
                    </div>
                    {(() => {
                      const playerVotedEmotion = lastResult.votes[playerName];
                      const correctEmotionId = lastResult.correctEmotionId;
                      const isCorrect = correctEmotionId ? playerVotedEmotion === correctEmotionId : false;
                      if (isCorrect) {
                        return <p className="text-green-700 text-sm mt-2 font-medium">{t.game.pointsEarned}</p>;
                      } else {
                        return <p className="text-red-700 text-sm mt-2 font-medium">{t.game.noPointsThisTime}</p>;
                      }
                    })()}
                  </div>
                </div>
              )}
              
              {/* Speaker Result */}
              {lastResult.votes && !lastResult.votes[playerName] && (
                <div className="bg-blue-50 p-6 rounded-lg text-center border border-blue-200">
                  <p className="text-lg font-semibold text-blue-700 mb-2">
                    {t.game.youWereSpeaker}
                  </p>
                  <p className="text-xl font-bold">
                    {t.game.correctAnswerLabel} {getEmotionNameById(lastResult.correctEmotionId || '')}
                  </p>
                </div>
              )}
              
              <div>
                <h3 className="font-semibold mb-2">{t.common.currentScore}:</h3>
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
                  <button
                    onClick={handleStartRound}
                    disabled={isStartingRound}
                    className={`w-full py-3 rounded-lg font-medium ${
                      isStartingRound
                        ? 'bg-gray-400 text-gray-600 cursor-not-allowed'
                        : 'bg-blue-600 text-white hover:bg-blue-700'
                    }`}
                  >
                    {isStartingRound ? t.game.preparing : t.game.nextRoundArrow}
                  </button>
                </div>
              )}

              {lastResult.isGameComplete && (
                <div className="text-center bg-yellow-50 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold text-yellow-800 mb-2">
                    {t.game.gameEndEmoji}
                  </h3>
                  <p className="text-yellow-700">
                    {lastResult.completedCycles || Math.floor((lastResult.completedRounds || 0) / roomState.players.length)}/{lastResult.maxCycles || lastResult.maxRounds}{t.game.cyclesCompleted}
                  </p>
                </div>
              )}
            </div>
          )}

          {gameComplete && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-center text-gold">{t.game.finalResultsEmoji}</h2>
              
              <div className="bg-gradient-to-br from-yellow-50 to-orange-50 p-6 rounded-lg border-2 border-yellow-200">
                <h3 className="text-xl font-semibold mb-4 text-center">{t.game.ranking}</h3>
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
                          {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `${player.rank}${t.common.rank}`}
                        </span>
                        <span className={`font-semibold ${
                          player.name === playerName ? 'text-blue-600' : 'text-gray-800'
                        }`}>
                          {player.name}
                          {player.name === playerName && ` (${t.common.you})`}
                        </span>
                      </div>
                      <span className="text-xl font-bold text-gray-800">{player.score}pt</span>
                    </div>
                  ))}
                </div>
                
                <div className="mt-6 text-center text-gray-600">
                  <p>{t.game.allRoundsComplete.replace('{rounds}', gameComplete.totalRounds.toString())}</p>
                </div>
              </div>

              {isHost && (
                <div className="space-y-4">
                  {/* Settings Section for Next Game */}
                  <button
                    onClick={() => {
                      setGameComplete(null);
                      setLastResult(null);
                      restartGame();
                    }}
                    className="w-full bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 font-medium"
                  >
                    {t.game.playAgainEmoji}
                  </button>
                  <p className="text-center text-sm text-gray-500">
                    {t.game.resetMessage}
                  </p>
                </div>
              )}

              {!isHost && (
                <div className="text-center text-gray-600">
                  <p>{t.game.waitingForNextGame}</p>
                </div>
              )}
            </div>
          )}
        </div>
        </div>
      </div>
    </>
  );
}