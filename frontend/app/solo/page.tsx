'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getApiUrl } from '@/utils/api';
import { getOrCreatePlayerId } from '@/utils/playerStorage';

// Edge Runtime 対応
export const runtime = 'edge';

// 感情の定義
const EMOTIONS = [
  { id: 0, label: '中立', english: 'neutral', color: 'bg-gray-500', description: '平常心で話してください' },
  { id: 1, label: '喜び', english: 'happy', color: 'bg-yellow-500', description: '嬉しい気持ちで話してください' },
  { id: 2, label: '怒り', english: 'angry', color: 'bg-red-500', description: '怒った気持ちで話してください' },
  { id: 3, label: '悲しみ', english: 'sad', color: 'bg-blue-500', description: '悲しい気持ちで話してください' }
];

// ゲームの状態
type GameState = 'start' | 'loadingDialogue' | 'ready' | 'recording' | 'processing' | 'roundResult' | 'finalResult';

interface RoundData {
  round: number;
  emotion: string;
  emotionId: number;
  dialogue: string;
  score: number;
  predictedEmotion: string;
  isCorrect: boolean;
}

interface GameResult {
  rounds: RoundData[];
  totalScore: number;
  averageScore: number;
  bestRound: number;
}

export default function SoloPage() {
  const [gameState, setGameState] = useState<GameState>('start');
  const [currentRound, setCurrentRound] = useState(1);
  const [currentEmotion, setCurrentEmotion] = useState<number | null>(null);
  const [currentDialogue, setCurrentDialogue] = useState<string>('');
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [rounds, setRounds] = useState<RoundData[]>([]);
  const [finalResult, setFinalResult] = useState<GameResult | null>(null);
  const [highScore, setHighScore] = useState(0);
  const [deviceId, setDeviceId] = useState<string>('');
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const router = useRouter();

  // 端末固定IDとハイスコアをlocalStorageから読み込み
  useEffect(() => {
    // マルチプレイと同じplayerIDを使用して統一性を保つ
    const playerId = getOrCreatePlayerId();
    setDeviceId(playerId);
    
    // ハイスコア読み込み
    const savedHighScore = localStorage.getItem('emoguchi-solo-highscore');
    if (savedHighScore) {
      setHighScore(parseInt(savedHighScore, 10));
    }
  }, []);

  // ハイスコアをlocalStorageに保存
  const updateHighScore = (score: number) => {
    if (score > highScore) {
      setHighScore(score);
      localStorage.setItem('emoguchi-solo-highscore', score.toString());
      return true; // 新記録
    }
    return false;
  };

  // ゲーム開始：セリフと感情を取得
  const startGame = async () => {
    setGameState('loadingDialogue');
    setCurrentRound(1);
    setRounds([]);
    await loadNextRound();
  };

  // 次のラウンド開始：LLMからセリフと感情を取得
  const loadNextRound = async () => {
    try {
      setGameState('loadingDialogue');
      
      const response = await fetch(`${getApiUrl()}/api/v1/solo/dialogue`);
      if (!response.ok) {
        throw new Error('セリフの取得に失敗しました');
      }
      
      const data = await response.json();
      setCurrentEmotion(data.emotion_id);
      setCurrentDialogue(data.dialogue);
      setGameState('ready');
      
    } catch (error) {
      console.error('セリフ生成エラー:', error);
      alert('セリフの生成に失敗しました。もう一度お試しください。');
      setGameState('start');
    }
  };

  // 録音開始
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        } 
      });
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      audioChunksRef.current = [];
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { 
          type: 'audio/webm;codecs=opus' 
        });
        setAudioBlob(audioBlob);
        
        // ストリームを停止
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start(100);
      setIsRecording(true);
      setGameState('recording');
      
    } catch (error) {
      console.error('録音の開始に失敗しました:', error);
      alert('マイクへのアクセスが拒否されました。ブラウザの設定を確認してください。');
    }
  };

  // 録音停止
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // AI推論を実行
  const submitAudio = async () => {
    if (!audioBlob || currentEmotion === null) return;
    
    setGameState('processing');
    
    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'recorded.wav');
      formData.append('target_emotion', currentEmotion.toString());
      formData.append('device_id', deviceId);  // 端末固定ID追加
      
      const response = await fetch(`${getApiUrl()}/api/v1/solo/predict`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error('推論APIの呼び出しに失敗しました');
      }
      
      const data = await response.json();
      console.log('🔍 API response:', data); // デバッグ用
      
      // 現在のラウンドデータを作成
      const roundData: RoundData = {
        round: currentRound,
        emotion: EMOTIONS[currentEmotion].label,
        emotionId: currentEmotion,
        dialogue: currentDialogue,
        score: data.score ?? 0,
        predictedEmotion: data.emotion || '不明',
        isCorrect: data.is_correct ?? false
      };
      
      // ラウンドデータを追加
      const newRounds = [...rounds, roundData];
      setRounds(newRounds);
      setGameState('roundResult');
      
      // 3回目でも最終結果の計算はボタンクリック時に行う
      
    } catch (error) {
      console.error('推論処理でエラーが発生しました:', error);
      alert('推論処理でエラーが発生しました。もう一度お試しください。');
      setGameState('start');
    }
  };

  // 最終結果を計算
  const calculateFinalResult = (allRounds: RoundData[]) => {
    const totalScore = allRounds.reduce((sum, round) => sum + round.score, 0);
    const averageScore = Math.round(totalScore / allRounds.length);
    const bestRound = allRounds.reduce((best, round) => 
      round.score > best.score ? round : best
    ).round;
    
    const result: GameResult = {
      rounds: allRounds,
      totalScore,
      averageScore,
      bestRound
    };
    
    setFinalResult(result);
    updateHighScore(totalScore);
    setGameState('finalResult');
  };

  // 次のラウンドに進む
  const nextRound = () => {
    setCurrentRound(prev => prev + 1);
    setAudioBlob(null);
    setIsRecording(false);
    loadNextRound();
  };

  // 録音やり直し
  const retryRecording = () => {
    setAudioBlob(null);
    setIsRecording(false);
    setGameState('ready'); // 同じラウンドの準備画面に戻る
  };

  // ゲームリセット
  const resetGame = () => {
    setGameState('start');
    setCurrentRound(1);
    setCurrentEmotion(null);
    setCurrentDialogue('');
    setIsRecording(false);
    setAudioBlob(null);
    setRounds([]);
    setFinalResult(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-rose-50 dark:from-slate-900 dark:via-purple-900 dark:to-pink-900 p-4 transition-colors duration-300">
      <div className="max-w-4xl mx-auto">
        {/* ヘッダー */}
        <div className="text-center mb-8">
          {/* ホームボタン */}
          <div className="flex justify-between items-center mb-6">
            <button
              onClick={() => router.push('/')}
              className="bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50 transition-all shadow-sm flex items-center"
            >
              <span className="mr-2">←</span>
              ホーム
            </button>
            <div className="flex-1" />
          </div>
          
          <h1 className="text-4xl font-bold text-gray-800 dark:text-white mb-2">
            🎭 ソロ感情演技モード
          </h1>
          <p className="text-gray-600 dark:text-gray-300 mb-4">
            AIが指定した感情を演技して、あなたの演技力をスコア化します
          </p>
          
          {/* ハイスコア・進行状況表示 */}
          <div className="flex justify-center items-center gap-4 mb-6">
            <div className="bg-white dark:bg-slate-800 border border-gray-300 dark:border-slate-600 rounded-full px-4 py-2 flex items-center shadow-lg">
              <span className="text-yellow-500 mr-2">🏆</span>
              ハイスコア: {highScore}点
            </div>
            {(gameState !== 'start') && (
              <div className="bg-purple-500 dark:bg-purple-600 text-white rounded-full px-4 py-2 shadow-lg">
                ラウンド {currentRound}/3
              </div>
            )}
            {gameState === 'finalResult' && finalResult && (
              <div className="bg-green-500 dark:bg-green-600 text-white rounded-full px-4 py-2 shadow-lg">
                合計: {finalResult.totalScore}点
              </div>
            )}
          </div>
        </div>

        {/* ゲーム開始画面 */}
        {gameState === 'start' && (
          <div className="max-w-2xl mx-auto bg-white rounded-2xl shadow-lg overflow-hidden">
            <div className="bg-gradient-to-r from-purple-600 to-pink-600 text-white p-6">
              <h2 className="text-2xl font-bold mb-2">ソロ演技チャレンジ</h2>
              <p className="text-purple-100">
                AIがランダムに選んだ感情とセリフで3回演技します
              </p>
              <p className="text-purple-100 text-sm mt-2">
                合計スコアで競いましょう！
              </p>
            </div>
            <div className="p-6 text-center">
              <div className="mb-6">
                <div className="text-lg font-semibold mb-4">🎲 ゲームルール</div>
                <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-700">
                  <p className="mb-2">• AIがランダムに感情とセリフを生成</p>
                  <p className="mb-2">• その感情でセリフを演技して録音</p>
                  <p className="mb-2">• AIがあなたの演技を100点満点で采点</p>
                  <p>• 3回演技の合計スコアで最終結果が決まります</p>
                </div>
              </div>
              
              <button
                onClick={startGame}
                className="w-full bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white py-4 px-6 rounded-xl transition-all duration-200 font-medium text-lg shadow-lg hover:shadow-xl transform hover:scale-[1.02] active:scale-[0.98] flex items-center justify-center focus:ring-2 focus:ring-green-500 focus:ring-offset-2 dark:focus:ring-offset-slate-800"
              >
                <span className="mr-2">🎆</span>
                チャレンジ開始！
              </button>
            </div>
          </div>
        )}

        {/* セリフ読み込み中 */}
        {gameState === 'loadingDialogue' && (
          <div className="max-w-2xl mx-auto bg-white rounded-2xl shadow-lg overflow-hidden">
            <div className="p-12 text-center">
              <div className="animate-spin w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full mx-auto mb-4" />
              <div className="text-xl font-semibold mb-2">セリフを生成中...</div>
              <p className="text-gray-600">
                AIがラウンド{currentRound}のセリフと感情を選んでいます
              </p>
              <button
                onClick={() => router.push('/')}
                className="mt-4 text-gray-500 hover:text-gray-700 underline"
              >
                ホームに戻る
              </button>
            </div>
          </div>
        )}

        {/* 演技準備画面 */}
        {gameState === 'ready' && currentEmotion !== null && (
          <div className="max-w-2xl mx-auto bg-white rounded-2xl shadow-lg overflow-hidden">
            <div className="bg-gradient-to-r from-blue-500 to-purple-500 text-white p-6 text-center">
              <h2 className="text-2xl font-bold mb-2">
                ラウンド {currentRound}/3
              </h2>
              <p className="text-blue-100">
                以下のセリフを「{EMOTIONS[currentEmotion].label}」の感情で演技してください
              </p>
            </div>
            <div className="p-6 text-center">
              <div className="mb-8">
                <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
                  <div className="text-sm text-gray-600 mb-1">セリフ</div>
                  <div className="text-2xl font-bold text-gray-800 mb-2">{currentDialogue}</div>
                </div>
                
                <div className="flex items-center justify-center gap-4 mb-6">
                  <div className="text-center">
                    <div className="text-sm text-gray-600 mb-1">演技する感情</div>
                    <div className={`w-12 h-12 rounded-full ${EMOTIONS[currentEmotion].color} mx-auto mb-2`} />
                    <div className="font-semibold text-lg">{EMOTIONS[currentEmotion].label}</div>
                    <div className="text-sm text-gray-600">
                      {EMOTIONS[currentEmotion].description}
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="flex gap-4 justify-center">
                <button
                  onClick={startRecording}
                  className="bg-gradient-to-r from-red-500 to-red-600 text-white py-4 px-6 rounded-xl hover:from-red-600 hover:to-red-700 transition-all font-medium text-lg shadow-lg flex items-center"
                >
                  <span className="mr-2">🎤</span>
                  録音開始
                </button>
                <button
                  onClick={() => router.push('/')}
                  className="border border-gray-300 text-gray-700 py-4 px-6 rounded-xl hover:bg-gray-50 transition-all font-medium text-lg shadow-lg"
                >
                  ホーム
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 録音中画面 */}
        {gameState === 'recording' && currentEmotion !== null && (
          <div className="max-w-2xl mx-auto bg-white rounded-2xl shadow-lg overflow-hidden">
            <div className="bg-gradient-to-r from-red-500 to-pink-500 text-white p-6 text-center">
              <h2 className="text-2xl font-bold mb-2">
                {currentDialogue}
              </h2>
              <p className="text-red-100">
                「{EMOTIONS[currentEmotion].label}」の感情で演技中...
              </p>
            </div>
            <div className="p-6 text-center">
              <div className="mb-8">
                <div className={`w-24 h-24 rounded-full ${EMOTIONS[currentEmotion].color} mx-auto mb-4 animate-pulse`} />
                <div className="text-lg font-semibold mb-2">録音中...</div>
                {isRecording && (
                  <div className="flex justify-center">
                    <div className="w-4 h-4 bg-red-500 rounded-full animate-pulse" />
                  </div>
                )}
              </div>
              
              <button
                onClick={stopRecording}
                disabled={!isRecording}
                className="bg-red-500 hover:bg-red-600 disabled:bg-gray-400 disabled:cursor-not-allowed text-white py-3 px-6 rounded-xl transition-all font-medium text-lg shadow-lg flex items-center justify-center mx-auto mb-6"
              >
                <span className="mr-2">🚫</span>
                録音停止
              </button>
              
              {audioBlob && !isRecording && (
                <div className="mt-6">
                  <p className="mb-4">録音完了！送信して推論を実行しますか？</p>
                  <div className="flex gap-4 justify-center">
                    <button 
                      onClick={submitAudio}
                      className="bg-gradient-to-r from-green-500 to-green-600 text-white py-3 px-6 rounded-xl hover:from-green-600 hover:to-green-700 transition-all font-medium shadow-lg"
                    >
                      推論実行
                    </button>
                    <button 
                      onClick={retryRecording}
                      className="border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 py-3 px-6 rounded-xl hover:bg-gray-50 dark:hover:bg-slate-700 transition-all font-medium shadow-lg"
                    >
                      録音やり直し
                    </button>
                    <button
                      onClick={() => router.push('/')}
                      className="text-gray-500 hover:text-gray-700 py-3 px-6 rounded-xl hover:bg-gray-50 transition-all"
                    >
                      ホーム
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 処理中画面 */}
        {gameState === 'processing' && (
          <div className="max-w-2xl mx-auto bg-white rounded-2xl shadow-lg overflow-hidden">
            <div className="p-12 text-center">
              <div className="animate-spin w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4" />
              <div className="text-xl font-semibold mb-2">AI推論中...</div>
              <p className="text-gray-600">
                あなたの音声を分析しています
              </p>
              <button
                onClick={() => router.push('/')}
                className="mt-4 text-gray-500 hover:text-gray-700 underline"
              >
                ホームに戻る
              </button>
            </div>
          </div>
        )}

        {/* ラウンド結果表示 */}
        {gameState === 'roundResult' && rounds.length > 0 && (
          <div className="max-w-2xl mx-auto bg-white rounded-2xl shadow-lg overflow-hidden">
            <div className="bg-gradient-to-r from-green-500 to-blue-500 text-white p-6 text-center">
              <h2 className="text-2xl font-bold">ラウンド{currentRound} 結果</h2>
            </div>
            <div className="p-6 text-center">
              {(() => {
                const lastRound = rounds[rounds.length - 1];
                return (
                  <>
                    <div className="mb-6">
                      <div className="bg-gray-50 rounded-lg p-4 mb-4">
                        <div className="text-sm text-gray-600 mb-1">セリフ</div>
                        <div className="text-lg font-semibold">{lastRound.dialogue}</div>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4 mb-6">
                        <div className="p-4 bg-blue-50 rounded-lg">
                          <div className="text-sm text-gray-600 mb-1">目標感情</div>
                          <div className={`w-8 h-8 rounded-full ${EMOTIONS[lastRound.emotionId].color} mx-auto mb-2`} />
                          <div className="font-semibold">{lastRound.emotion}</div>
                        </div>
                        <div className="p-4 bg-green-50 rounded-lg">
                          <div className="text-sm text-gray-600 mb-1">AI推論結果</div>
                          <div className="text-2xl mb-2">🤖</div>
                          <div className="font-semibold">{lastRound.predictedEmotion}</div>
                        </div>
                      </div>
                      
                      <div className="mb-6">
                        <div className="text-4xl font-bold mb-2">
                          <span className={`${lastRound.score >= 80 ? 'text-green-600' : lastRound.score >= 60 ? 'text-yellow-600' : 'text-red-600'}`}>
                            {lastRound.score}
                          </span>
                          <span className="text-xl text-gray-400">点</span>
                        </div>
                        
                        <div className="mb-4">
                          {lastRound.score >= 90 && (
                            <div className="bg-yellow-400 text-black px-4 py-2 rounded-full inline-block font-medium">
                              🏆 完璧！
                            </div>
                          )}
                          {lastRound.score >= 80 && lastRound.score < 90 && (
                            <div className="bg-green-500 text-white px-4 py-2 rounded-full inline-block font-medium">
                              🎉 素晴らしい！
                            </div>
                          )}
                          {lastRound.score >= 60 && lastRound.score < 80 && (
                            <div className="bg-yellow-500 text-white px-4 py-2 rounded-full inline-block font-medium">
                              👍 良い演技！
                            </div>
                          )}
                          {lastRound.score >= 40 && lastRound.score < 60 && (
                            <div className="bg-orange-500 text-white px-4 py-2 rounded-full inline-block font-medium">
                              😊 まずまず
                            </div>
                          )}
                          {lastRound.score < 40 && (
                            <div className="bg-red-500 text-white px-4 py-2 rounded-full inline-block font-medium">
                              💪 練習あるのみ！
                            </div>
                          )}
                        </div>
                        
                        <div className="text-sm">
                          正解: {lastRound.isCorrect ? '✅' : '❌'}
                          {lastRound.isCorrect ? 
                            ' 感情を正確に演技できました！' : 
                            ' 異なる感情として認識されました'}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex gap-4 justify-center">
                      {currentRound < 3 ? (
                        <button 
                          onClick={nextRound}
                          className="bg-gradient-to-r from-purple-500 to-purple-600 text-white py-3 px-6 rounded-xl hover:from-purple-600 hover:to-purple-700 transition-all font-medium shadow-lg flex items-center"
                        >
                          <span className="mr-2">➡️</span>
                          次のラウンドへ
                        </button>
                      ) : (
                        <button 
                          onClick={() => calculateFinalResult(rounds)}
                          className="bg-gradient-to-r from-green-500 to-green-600 text-white py-3 px-6 rounded-xl hover:from-green-600 hover:to-green-700 transition-all font-medium shadow-lg flex items-center"
                        >
                          <span className="mr-2">🏆</span>
                          最終結果を見る
                        </button>
                      )}
                      <button
                        onClick={() => router.push('/')}
                        className="text-gray-500 hover:text-gray-700 py-3 px-6 rounded-xl hover:bg-gray-50 transition-all"
                      >
                        ホーム
                      </button>
                    </div>
                  </>
                );
              })()}
            </div>
          </div>
        )}

        {/* 最終結果表示 */}
        {gameState === 'finalResult' && finalResult && (
          <div className="max-w-4xl mx-auto bg-white rounded-2xl shadow-lg overflow-hidden">
            <div className="bg-gradient-to-r from-yellow-400 to-orange-500 text-white p-6 text-center">
              <h2 className="text-3xl font-bold mb-2">🏆 最終結果</h2>
              <p className="text-yellow-100">
                3ラウンドのチャレンジが完了しました！
              </p>
            </div>
            <div className="p-6">
              {/* 合計スコア */}
              <div className="text-center mb-8">
                <div className="text-6xl font-bold mb-2">
                  <span className={`${finalResult.totalScore >= 240 ? 'text-green-600' : finalResult.totalScore >= 180 ? 'text-yellow-600' : 'text-red-600'}`}>
                    {finalResult.totalScore}
                  </span>
                  <span className="text-2xl text-gray-400">点 / 300点</span>
                </div>
                
                <div className="mb-4">
                  {finalResult.totalScore >= 280 && (
                    <div className="bg-gradient-to-r from-yellow-400 to-yellow-600 text-black text-xl px-6 py-3 rounded-full inline-block font-bold">
                      🏆 伝説の演技者！（ほぼ満点！）
                    </div>
                  )}
                  {finalResult.totalScore >= 240 && finalResult.totalScore < 280 && (
                    <div className="bg-green-500 text-white text-xl px-6 py-3 rounded-full inline-block font-bold">
                      🎆 素晴らしい演技力！
                    </div>
                  )}
                  {finalResult.totalScore >= 180 && finalResult.totalScore < 240 && (
                    <div className="bg-yellow-500 text-white text-xl px-6 py-3 rounded-full inline-block font-bold">
                      👍 良い演技でした！
                    </div>
                  )}
                  {finalResult.totalScore >= 120 && finalResult.totalScore < 180 && (
                    <div className="bg-orange-500 text-white text-xl px-6 py-3 rounded-full inline-block font-bold">
                      😊 まずまずの成果！
                    </div>
                  )}
                  {finalResult.totalScore < 120 && (
                    <div className="bg-red-500 text-white text-xl px-6 py-3 rounded-full inline-block font-bold">
                      💪 練習あるのみ！
                    </div>
                  )}
                </div>
                
                {/* ハイスコア更新チェック */}
                {finalResult.totalScore > highScore && (
                  <div className="mb-6">
                    <div className="bg-gradient-to-r from-yellow-400 to-yellow-600 text-black text-xl px-6 py-3 rounded-full inline-block font-bold">
                      🎉 新記録達成！ 🎉
                    </div>
                    <div className="text-sm text-gray-600 mt-2">
                      前回のハイスコア: {highScore}点
                    </div>
                  </div>
                )}
                
                <div className="grid grid-cols-3 gap-4 mb-6">
                  <div className="bg-blue-50 rounded-lg p-4">
                    <div className="text-sm text-gray-600 mb-1">合計スコア</div>
                    <div className="text-2xl font-bold">{finalResult.totalScore}点</div>
                  </div>
                  <div className="bg-green-50 rounded-lg p-4">
                    <div className="text-sm text-gray-600 mb-1">平均スコア</div>
                    <div className="text-2xl font-bold">{finalResult.averageScore}点</div>
                  </div>
                  <div className="bg-yellow-50 rounded-lg p-4">
                    <div className="text-sm text-gray-600 mb-1">ベストラウンド</div>
                    <div className="text-2xl font-bold">第{finalResult.bestRound}ラウンド</div>
                  </div>
                </div>
              </div>
              
              {/* 各ラウンド詳細 */}
              <div className="mb-8">
                <h3 className="text-xl font-bold mb-4 text-center">ラウンド別詳細</h3>
                <div className="space-y-4">
                  {finalResult.rounds.map((round, index) => (
                    <div key={index} className="bg-gray-50 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="font-semibold">ラウンド{round.round}</div>
                        <div className="text-2xl font-bold">{round.score}点</div>
                      </div>
                      <div className="text-sm text-gray-600 mb-1">セリフ: 「{round.dialogue}」</div>
                      <div className="flex items-center gap-4 text-sm">
                        <span>目標: {round.emotion}</span>
                        <span>推論: {round.predictedEmotion}</span>
                        <span className={round.isCorrect ? 'text-green-600' : 'text-red-600'}>
                          {round.isCorrect ? '✅ 正解' : '❌ 不正解'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="flex gap-4 justify-center">
                <button 
                  onClick={resetGame}
                  className="bg-gradient-to-r from-purple-500 to-purple-600 text-white py-3 px-6 rounded-xl hover:from-purple-600 hover:to-purple-700 transition-all font-medium shadow-lg flex items-center"
                >
                  <span className="mr-2">🔄</span>
                  もう一度挑戦
                </button>
                <button 
                  onClick={() => router.push('/')}
                  className="border border-gray-300 text-gray-700 py-3 px-6 rounded-xl hover:bg-gray-50 transition-all font-medium shadow-lg"
                >
                  メインに戻る
                </button>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}