import { create } from 'zustand';
import type { Player, RoomState } from '../types';

interface RoomStore {
  room?: RoomState;
  players: Player[];
  setRoom: (room: RoomState) => void;
  addPlayer: (p: Player) => void;
}

export const useRoomStore = create<RoomStore>((set) => ({
  room: undefined,
  players: [],
  setRoom: (room) => set({ room, players: room.players }),
  addPlayer: (p) => set((state) => ({ players: [...state.players, p] })),
}));
