import React from 'react';
import { useMediaRecorder } from '../hooks/useMediaRecorder';
import { useLocaleStore } from '@/stores/localeStore';
import { translations } from '@/lib/translations';

interface AudioRecorderProps {
  onRecordingComplete: (audioBlob: Blob) => void;
  disabled?: boolean;
}

export const AudioRecorder: React.FC<AudioRecorderProps> = ({ 
  onRecordingComplete, 
  disabled = false 
}) => {
  const {
    isRecording,
    audioBlob,
    startRecording,
    stopRecording,
    clearRecording,
    error
  } = useMediaRecorder();

  const { locale } = useLocaleStore();
  const t = translations[locale];

  const handleStart = async () => {
    clearRecording();
    await startRecording();
  };

  const handleStop = () => {
    stopRecording();
  };

  const handleSubmit = () => {
    if (audioBlob) {
      onRecordingComplete(audioBlob);
    }
  };

  const handleRetry = () => {
    clearRecording();
  };

  return (
    <div className="bg-white rounded-lg p-6 shadow-lg border-2 border-gray-200">
      <h3 className="text-lg font-semibold mb-4 text-gray-800">
        {t.audio.recording}
      </h3>
      
      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          <div className="flex justify-between items-center">
            <span>{error}</span>
            <button
              onClick={() => {
                clearRecording();
                // Clear error and reset state
              }}
              className="ml-2 px-2 py-1 bg-red-500 hover:bg-red-600 text-white text-xs rounded transition-colors"
            >
              {t.audio.retryButton}
            </button>
          </div>
        </div>
      )}

      <div className="space-y-4">
        {!audioBlob && !isRecording && (
          <button
            onClick={handleStart}
            disabled={disabled}
            className="w-full bg-red-500 hover:bg-red-600 disabled:bg-gray-400 text-white font-bold py-3 px-6 rounded-lg transition-colors duration-200"
          >
            🎤 {t.audio.startRecording}
          </button>
        )}

        {isRecording && (
          <div className="text-center">
            <div className="mb-4">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-red-500 rounded-full animate-pulse">
                <div className="w-4 h-4 bg-white rounded-full"></div>
              </div>
              <p className="mt-2 text-red-600 font-medium">{t.audio.recordingInProgress}</p>
            </div>
            <button
              onClick={handleStop}
              className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-3 px-6 rounded-lg transition-colors duration-200"
            >
              ⏹️ {t.audio.stopRecording}
            </button>
          </div>
        )}

        {audioBlob && (
          <div className="space-y-3">
            <div className="text-center">
              <p className="text-green-600 font-medium mb-3">✅ {t.audio.recordingComplete}</p>
              <audio 
                controls 
                src={URL.createObjectURL(audioBlob)}
                className="w-full"
              />
            </div>
            <div className="flex space-x-3">
              <button
                onClick={handleSubmit}
                className="flex-1 bg-blue-500 hover:bg-blue-600 text-white font-bold py-3 px-6 rounded-lg transition-colors duration-200"
              >
                📤 {t.audio.send}
              </button>
              <button
                onClick={handleRetry}
                className="flex-1 bg-gray-500 hover:bg-gray-600 text-white font-bold py-3 px-6 rounded-lg transition-colors duration-200"
              >
                🔄 {t.audio.retry}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};