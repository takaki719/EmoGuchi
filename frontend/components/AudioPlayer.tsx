import React, { useRef, useState } from 'react';

interface AudioPlayerProps {
  audioUrl: string;
  speakerName?: string;
  isProcessed?: boolean;
}

export const AudioPlayer: React.FC<AudioPlayerProps> = ({ audioUrl, speakerName, isProcessed = false }) => {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reset error when audioUrl changes
  React.useEffect(() => {
    setError(null);
    setIsPlaying(false);
  }, [audioUrl]);

  const handlePlay = async () => {
    if (audioRef.current) {
      try {
        setError(null);
        await audioRef.current.play();
        setIsPlaying(true);
      } catch (err) {
        console.error('Error playing audio:', err);
        setError('音声の再生に失敗しました');
      }
    }
  };

  const handlePause = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
    }
  };

  const handleEnded = () => {
    setIsPlaying(false);
  };

  const handleError = () => {
    setError('音声ファイルを読み込めませんでした');
    setIsPlaying(false);
  };

  const handleRetry = () => {
    if (audioRef.current) {
      setError(null);
      setIsPlaying(false);
      // Force reload the audio element
      audioRef.current.load();
    }
  };

  return (
    <div className="bg-blue-50 p-4 rounded-lg border-2 border-blue-200">
      <div className="mb-3">
        <h4 className="font-semibold text-blue-800">
          {speakerName ? `${speakerName}の音声:` : 'スピーカーの音声:'}
        </h4>
        {isProcessed && (
          <p className="text-xs text-red-600 mt-1">
            🎯 音声加工済み（高難易度モード）
          </p>
        )}
      </div>
      
      {error && (
        <div className="mb-3 p-2 bg-red-100 border border-red-400 text-red-700 rounded text-sm">
          <div className="flex justify-between items-center">
            <span>{error}</span>
            <button
              onClick={handleRetry}
              className="ml-2 px-2 py-1 bg-red-500 hover:bg-red-600 text-white text-xs rounded transition-colors"
            >
              再試行
            </button>
          </div>
        </div>
      )}
      
      <audio
        ref={audioRef}
        src={audioUrl}
        onEnded={handleEnded}
        onError={handleError}
        className="w-full mb-3"
        controls
      />
      
      <div className="flex space-x-2">
        <button
          onClick={handlePlay}
          disabled={isPlaying}
          className="flex-1 bg-green-500 hover:bg-green-600 disabled:bg-gray-400 text-white font-bold py-2 px-4 rounded transition-colors"
        >
          {isPlaying ? '▶️ 再生中...' : '▶️ 再生'}
        </button>
        <button
          onClick={handlePause}
          disabled={!isPlaying}
          className="flex-1 bg-gray-500 hover:bg-gray-600 disabled:bg-gray-400 text-white font-bold py-2 px-4 rounded transition-colors"
        >
          ⏸️ 停止
        </button>
      </div>
    </div>
  );
};