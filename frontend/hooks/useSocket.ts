import { useEffect, useCallback } from 'react';
import { socketClient } from '@/socket/client';
import { useGameStore } from '@/stores/gameStore';
import { RoomState, Round, RoundResult } from '@/types/game';

export const useSocket = () => {
  console.log('🚀 useSocket: Function called');
  
  let store;
  try {
    console.log('🚀 useSocket: About to call useGameStore...');
    store = useGameStore();
    console.log('🚀 useSocket: useGameStore successful');
  } catch (error) {
    console.error('❌ useSocket: useGameStore failed:', error);
    throw error;
  }

  useEffect(() => {
    console.log('🚀 useSocket: useEffect running');
    console.log('🚀 useSocket: Setting up socket connection');
    console.log('🚀 useSocket: Process env API URL:', process.env.NEXT_PUBLIC_API_URL);
    console.log('🚀 useSocket: About to call socketClient.connect()');
    
    const socket = socketClient.connect();
    
    console.log('🚀 useSocket: Socket returned from connect():', socket);
    console.log('🚀 useSocket: Socket type:', typeof socket);
    console.log('🚀 useSocket: Socket connected:', socket?.connected);

    // Connection events
    socket.on('connect', () => {
      console.log('useSocket: Connected to server');
      store.setConnected(true);
      store.setError(null);
    });

    socket.on('disconnect', () => {
      console.log('useSocket: Disconnected from server');
      store.setConnected(false);
    });

    socket.on('connect_error', (error: any) => {
      console.error('useSocket: Connection error:', error);
      store.setError(`Connection failed: ${error.message || error}`);
    });

    socket.on('connected', (data) => {
      console.log('Server message:', data.message);
    });

    // Room events
    socket.on('room_state', (data: RoomState) => {
      store.setRoomState(data);
      
      // Only clear game complete state when returning to waiting phase
      // lastResult should remain visible until manually cleared
      if (data.phase === 'waiting') {
        store.setGameComplete(null);
      }
    });

    socket.on('player_joined', (data) => {
      console.log(`${data.playerName} joined the room`);
      // Room state will be updated via room_state event
    });

    socket.on('player_reconnected', (data) => {
      console.log(`${data.playerName} reconnected to the room`);
      // Room state will be updated via room_state event
    });

    socket.on('player_left', (data) => {
      console.log(`${data.playerName} left the room`);
      // Room state will be updated via room_state event
    });

    socket.on('left_room', (data) => {
      console.log('Successfully left room:', data.message);
      store.reset(); // Clear all game state
    });

    socket.on('player_disconnected', (data) => {
      console.log(`${data.playerName} disconnected`);
    });

    // Round events
    socket.on('round_start', (data) => {
      console.log('🎮 round_start event received:', data);
      const round: Round = {
        id: data.roundId,
        phrase: data.phrase,
        emotion_id: '', // Hidden from listeners
        speaker_name: data.speakerName,
        voting_choices: data.votingChoices || []
      };
      console.log('🎮 Created round object:', round);
      store.setCurrentRound(round);
      store.setLastResult(null); // Clear previous round result when new round starts
      
      console.log('🎮 Current player name in store:', store.playerName);
      console.log('🎮 Round speaker name:', round.speaker_name);
    });

    socket.on('speaker_emotion', (data: any) => {
      console.log('🎭 speaker_emotion event received:', data);
      
      // For now, just process all speaker emotions to ensure functionality
      console.log('✅ Processing speaker_emotion (simplified)');
      store.setSpeakerEmotion(data.emotionName || data.emotionId);
    });

    socket.on('round_result', (data: RoundResult) => {
      console.log('Received round_result:', data);
      console.log('correct_emotion:', data.correct_emotion);
      console.log('correctEmotionId:', data.correctEmotionId);
      store.setLastResult(data);
      store.setCurrentRound(null);
      store.setSpeakerEmotion(null);
    });

    socket.on('game_complete', (data) => {
      store.setGameComplete(data);
    });

    // Audio events
    socket.on('audio_received', (data) => {
      console.log('🎵 audio_received event received:', data);
      console.log('Audio data type:', typeof data.audio, 'size:', data.audio?.byteLength || 'unknown');
      console.log('Audio data constructor:', data.audio?.constructor?.name);
      
      try {
        let audioBlob;
        
        // Handle different audio data types
        if (data.audio instanceof ArrayBuffer) {
          console.log('🎵 Converting ArrayBuffer to Blob');
          audioBlob = new Blob([data.audio], { type: 'audio/webm;codecs=opus' });
        } else if (data.audio && (data.audio as any).constructor?.name === 'Uint8Array') {
          console.log('🎵 Converting Uint8Array to Blob');
          audioBlob = new Blob([(data.audio as any).buffer], { type: 'audio/webm;codecs=opus' });
        } else if (data.audio && typeof data.audio === 'object' && (data.audio as any).data) {
          console.log('🎵 Converting object with data property to Blob');
          const uint8Array = new Uint8Array((data.audio as any).data);
          audioBlob = new Blob([uint8Array], { type: 'audio/webm;codecs=opus' });
        } else {
          console.log('🎵 Unknown audio data format, trying direct conversion');
          audioBlob = new Blob([data.audio], { type: 'audio/webm;codecs=opus' });
        }
        
        console.log('🎵 Created blob size:', audioBlob.size, 'type:', audioBlob.type);
        
        const audioUrl = URL.createObjectURL(audioBlob);
        store.setAudioUrl(audioUrl);
        store.setAudioProcessed(data.is_processed || false);
        console.log('✅ Audio URL created successfully:', audioUrl);
        console.log('🎯 Audio processed:', data.is_processed);
        
      } catch (error) {
        console.error('❌ Error creating audio URL:', error);
        console.error('❌ Audio data details:', data.audio);
        store.setError('音声データの処理に失敗しました');
      }
    });

    // Debug: Listen for all events
    socket.onAny((eventName, ...args) => {
      console.log('📡 Socket event received:', eventName, args);
      if (eventName === 'audio_received') {
        console.log('🎵 AUDIO_RECEIVED EVENT DETECTED!', args);
      }
    });

    // Debug: Listen for outgoing events too
    const originalEmit = socket.emit;
    socket.emit = function(eventName: string, ...args: any[]) {
      console.log('📤 Socket event SENT:', eventName, args);
      return (originalEmit as any).apply(socket, [eventName, ...args]);
    };

    // Error handling
    socket.on('error', (data) => {
      store.setError(`${data.code}: ${data.message}`);
    });

    return () => {
      socket.off('connect');
      socket.off('disconnect');
      socket.off('connect_error');
      socket.off('connected');
      socket.off('room_state');
      socket.off('player_joined');
      socket.off('player_reconnected');
      socket.off('player_left');
      socket.off('left_room');
      socket.off('player_disconnected');
      socket.off('round_start');
      socket.off('speaker_emotion');
      socket.off('round_result');
      socket.off('game_complete');
      socket.off('audio_received');
      socket.offAny();
      socket.off('error');
    };
  }, []); // Keep empty dependency array to avoid reconnection loops

  const joinRoom = useCallback((roomId: string, playerName: string) => {
    const socket = socketClient.getSocket();
    if (socket) {
      socket.emit('join_room', { roomId, playerName });
    }
  }, []);

  const startRound = useCallback(() => {
    const socket = socketClient.getSocket();
    if (socket) {
      socket.emit('start_round', {});
    }
  }, []);

  const submitVote = useCallback((roundId: string, emotionId: string) => {
    const socket = socketClient.getSocket();
    if (socket) {
      socket.emit('submit_vote', { roundId, emotionId });
    }
  }, []);

  const leaveRoom = useCallback(() => {
    const socket = socketClient.getSocket();
    if (socket) {
      socket.emit('leave_room', {});
    }
  }, []);

  const restartGame = useCallback(() => {
    const socket = socketClient.getSocket();
    if (socket) {
      socket.emit('restart_game', {});
    }
  }, []);

  const sendAudio = useCallback((audioBlob: Blob) => {
    const socket = socketClient.getSocket();
    console.log('🔥 sendAudio called, socket available:', !!socket, 'connected:', socket?.connected);
    console.log('🔥 Socket ID:', socket?.id);
    
    if (socket && socket.connected) {
      const reader = new FileReader();
      reader.onload = () => {
        const arrayBuffer = reader.result as ArrayBuffer;
        console.log('🔥 Sending audio data, size:', arrayBuffer.byteLength);
        console.log('🔥 Audio data type:', typeof arrayBuffer);
        console.log('🔥 Audio data preview:', new Uint8Array(arrayBuffer.slice(0, 10)));
        
        // Send the audio_send event with detailed logging
        try {
          console.log('🔥 About to emit audio_send event...');
          socket.emit('audio_send', { audio: arrayBuffer });
          console.log('✅ audio_send event emitted successfully with data size:', arrayBuffer.byteLength);
          
          // Add timeout to check if event was processed
          setTimeout(() => {
            console.log('🔥 5 seconds passed since audio_send - checking for response...');
          }, 5000);
          
        } catch (error) {
          console.error('❌ Error emitting audio_send:', error);
        }
      };
      reader.onerror = (error) => {
        console.error('❌ Error reading audio blob:', error);
      };
      reader.readAsArrayBuffer(audioBlob);
    } else {
      console.error('❌ Socket not available or not connected for audio sending. Connected:', socket?.connected);
    }
  }, []);

  return {
    socket: socketClient.getSocket(),
    isConnected: socketClient.isConnected(),
    joinRoom,
    startRound,
    submitVote,
    leaveRoom,
    restartGame,
    sendAudio
  };
};