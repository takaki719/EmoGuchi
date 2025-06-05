import { io, Socket } from 'socket.io-client';
import type { Player } from '../types';

export interface RoundStartPayload {
  roundId: string;
  phrase: string;
}

export interface RoundResultPayload {
  roundId: string;
  correctEmotion?: string;
  scores: Record<string, number>;
}

let socket: Socket | null = null;

export function connect(roomId: string, playerName: string) {
  socket = io(process.env.NEXT_PUBLIC_BACKEND_URL || '', {
    path: '/ws',
    auth: { roomId, playerName },
  });
  return socket;
}

export const disconnect = () => {
  socket?.disconnect();
  socket = null;
};

export const onPlayerJoined = (handler: (p: Player) => void) => {
  socket?.on('player_joined', handler);
};

export const onRoundStart = (handler: (payload: RoundStartPayload) => void) => {
  socket?.on('round_start', handler);
};

export const onRoundResult = (handler: (payload: RoundResultPayload) => void) => {
  socket?.on('round_result', handler);
};

export const joinRoom = (roomId: string, playerName: string) => {
  socket?.emit('join_room', { roomId, playerName });
};

export const submitVote = (roundId: string, emotionId: string) => {
  socket?.emit('submit_vote', { roundId, emotionId });
};
