import React, { useRef, useState } from 'react';

interface AudioPlayerProps {
  audioUrl: string;
  speakerName?: string;
}

export const AudioPlayer: React.FC<AudioPlayerProps> = ({ audioUrl, speakerName }) => {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  return (
    <div className="bg-blue-50 p-4 rounded-lg border-2 border-blue-200">
      <h4 className="font-semibold text-blue-800 mb-3">
        {speakerName ? `${speakerName}の音声:` : 'スピーカーの音声:'}
      </h4>
      
      {error && (
        <div className="mb-3 p-2 bg-red-100 border border-red-400 text-red-700 rounded text-sm">
          {error}
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