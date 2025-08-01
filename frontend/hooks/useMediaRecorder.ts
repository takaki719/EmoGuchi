import { useState, useRef, useCallback } from 'react';

export interface UseMediaRecorderReturn {
  isRecording: boolean;
  audioBlob: Blob | null;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  clearRecording: () => void;
  error: string | null;
}

export const useMediaRecorder = (): UseMediaRecorderReturn => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = useCallback(async () => {
    try {
      setError(null);
      
      // Clean up any existing recording state
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
      
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        } 
      });
      
      // Check if MediaRecorder is supported with the preferred format
      let mimeType = 'audio/webm;codecs=opus';
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        // Fallback to other formats
        if (MediaRecorder.isTypeSupported('audio/webm')) {
          mimeType = 'audio/webm';
        } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
          mimeType = 'audio/mp4';
        } else {
          mimeType = ''; // Use default
        }
        console.log('🎤 Using fallback mime type:', mimeType);
      }
      
      const mediaRecorder = new MediaRecorder(stream, 
        mimeType ? { mimeType } : undefined
      );
      
      chunksRef.current = [];
      
      mediaRecorder.ondataavailable = (event) => {
        console.log('🎤 Data available:', event.data.size, 'bytes');
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = () => {
        console.log('🎤 Recording stopped, chunks:', chunksRef.current.length);
        if (chunksRef.current.length === 0) {
          setError('録音データが取得できませんでした。再試行してください。');
          return;
        }
        
        const blob = new Blob(chunksRef.current, { 
          type: mimeType || 'audio/webm' 
        });
        console.log('🎤 Created blob:', blob.size, 'bytes, type:', blob.type);
        
        if (blob.size === 0) {
          setError('録音データが空です。マイクの接続を確認してください。');
          return;
        }
        
        setAudioBlob(blob);
        
        // Clean up stream
        stream.getTracks().forEach(track => {
          track.stop();
          console.log('🎤 Stopped track:', track.kind);
        });
      };
      
      mediaRecorder.onerror = (event: any) => {
        console.error('🎤 MediaRecorder error:', event.error);
        setError(`録音エラー: ${event.error?.message || '不明なエラー'}`);
        setIsRecording(false);
      };
      
      mediaRecorderRef.current = mediaRecorder;
      
      try {
        mediaRecorder.start(100); // Record in 100ms chunks
        setIsRecording(true);
        console.log('🎤 Recording started with mime type:', mimeType);
      } catch (startError) {
        console.error('🎤 Failed to start recording:', startError);
        setError('録音を開始できませんでした。ブラウザを再読み込みしてください。');
        stream.getTracks().forEach(track => track.stop());
      }
      
    } catch (err: any) {
      console.error('🎤 Recording setup failed:', err);
      if (err.name === 'NotAllowedError') {
        setError('マイクアクセスが拒否されました。ブラウザの設定を確認してください。');
      } else if (err.name === 'NotFoundError') {
        setError('マイクが見つかりません。マイクが接続されているか確認してください。');
      } else {
        setError(`録音エラー: ${err.message || '不明なエラー'}`);
      }
    }
  }, []);

  const stopRecording = useCallback(() => {
    console.log('🎤 stopRecording called, current state:', mediaRecorderRef.current?.state);
    
    if (mediaRecorderRef.current) {
      const recorder = mediaRecorderRef.current;
      
      if (recorder.state === 'recording') {
        try {
          recorder.stop();
          console.log('🎤 MediaRecorder stopped');
        } catch (error) {
          console.error('🎤 Error stopping recording:', error);
          setError('録音停止でエラーが発生しました。');
        }
      } else {
        console.warn('🎤 MediaRecorder not in recording state:', recorder.state);
      }
      
      setIsRecording(false);
    } else {
      console.warn('🎤 No MediaRecorder instance available');
      setIsRecording(false);
    }
  }, []);

  const clearRecording = useCallback(() => {
    console.log('🎤 clearRecording called');
    
    // Clean up MediaRecorder if it exists
    if (mediaRecorderRef.current) {
      const recorder = mediaRecorderRef.current;
      
      if (recorder.state === 'recording') {
        try {
          recorder.stop();
          console.log('🎤 Stopped recording during clear');
        } catch (error) {
          console.error('🎤 Error stopping recording during clear:', error);
        }
      }
      
      mediaRecorderRef.current = null;
    }
    
    // Clear chunks
    chunksRef.current = [];
    
    // Reset state
    setAudioBlob(null);
    setError(null);
    setIsRecording(false);
    
    console.log('🎤 Recording state cleared');
  }, []);

  return {
    isRecording,
    audioBlob,
    startRecording,
    stopRecording,
    clearRecording,
    error
  };
};