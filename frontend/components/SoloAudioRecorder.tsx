'use client';

import React, { useState, useRef } from 'react';
// import { Button } from '@/components/ui/button';
// import { Mic, MicOff, Play, Square } from 'lucide-react';

interface SoloAudioRecorderProps {
  onRecordingComplete: (audioBlob: Blob) => void;
  disabled?: boolean;
}

export default function SoloAudioRecorder({ onRecordingComplete, disabled = false }: SoloAudioRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

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
        const blob = new Blob(audioChunksRef.current, { 
          type: 'audio/webm;codecs=opus' 
        });
        setAudioBlob(blob);
        
        // Create URL for playback
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);
        
        // Notify parent component
        onRecordingComplete(blob);
        
        // ストリームを停止
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start(100);
      setIsRecording(true);
      
    } catch (error) {
      console.error('録音の開始に失敗しました:', error);
      alert('マイクへのアクセスが拒否されました。ブラウザの設定を確認してください。');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const resetRecording = () => {
    setAudioBlob(null);
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }
  };

  return (
    <div className="space-y-4">
      {/* 録音状態表示 */}
      <div className="text-center">
        {isRecording && (
          <div className="flex items-center justify-center mb-4">
            <div className="w-4 h-4 bg-red-500 rounded-full animate-pulse mr-2" />
            <span className="text-red-600 font-semibold">録音中...</span>
          </div>
        )}
        
        {audioBlob && !isRecording && (
          <div className="text-green-600 font-semibold mb-4">
            ✅ 録音完了
          </div>
        )}
      </div>

      {/* 録音コントロール */}
      <div className="flex justify-center gap-4">
        {!isRecording && !audioBlob && (
          <button
            onClick={startRecording}
            disabled={disabled}
            className="bg-red-500 hover:bg-red-600 disabled:opacity-50 text-white py-3 px-6 rounded-lg font-medium flex items-center justify-center transition-all"
          >
            🎤 録音開始
          </button>
        )}
        
        {isRecording && (
          <button
            onClick={stopRecording}
            className="bg-red-600 hover:bg-red-700 text-white py-3 px-6 rounded-lg font-medium flex items-center justify-center transition-all"
          >
            ⏹️ 録音停止
          </button>
        )}
        
        {audioBlob && !isRecording && (
          <>
            {/* 録音済み音声の再生 */}
            {audioUrl && (
              <audio controls className="mb-4">
                <source src={audioUrl} type="audio/webm" />
                お使いのブラウザは音声再生をサポートしていません。
              </audio>
            )}
            
            <button
              onClick={resetRecording}
              className="border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 py-3 px-6 rounded-lg font-medium hover:bg-gray-50 dark:hover:bg-slate-700 transition-all"
            >
              録り直し
            </button>
          </>
        )}
      </div>
    </div>
  );
}