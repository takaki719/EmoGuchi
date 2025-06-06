import { useEffect, useCallback } from 'react';
import { socketClient } from '@/socket/client';
import { useGameStore } from '@/stores/gameStore';
import { RoomState, Round, RoundResult } from '@/types/game';

export const useSocket = () => {
  const store = useGameStore();

  useEffect(() => {
    console.log('useSocket: Setting up socket connection');
    const socket = socketClient.connect();

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
    });

    socket.on('player_joined', (data) => {
      console.log(`${data.playerName} joined the room`);
      // Room state will be updated via room_state event
    });

    socket.on('player_reconnected', (data) => {
      console.log(`${data.playerName} reconnected to the room`);
      // Room state will be updated via room_state event
    });

    socket.on('player_disconnected', (data) => {
      console.log(`${data.playerName} disconnected`);
    });

    // Round events
    socket.on('round_start', (data) => {
      const round: Round = {
        id: data.roundId,
        phrase: data.phrase,
        emotion_id: '', // Hidden from listeners
        speaker_name: data.speakerName
      };
      store.setCurrentRound(round);
      store.setLastResult(null);
    });

    socket.on('speaker_emotion', (data) => {
      store.setSpeakerEmotion(data.emotionId);
    });

    socket.on('round_result', (data: RoundResult) => {
      store.setLastResult(data);
      store.setCurrentRound(null);
      store.setSpeakerEmotion(null);
    });

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
      socket.off('player_disconnected');
      socket.off('round_start');
      socket.off('speaker_emotion');
      socket.off('round_result');
      socket.off('error');
    };
  }, []); // 依存配列を空にして無限ループを防ぐ

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

  return {
    socket: socketClient.getSocket(),
    isConnected: socketClient.isConnected(),
    joinRoom,
    startRound,
    submitVote
  };
};