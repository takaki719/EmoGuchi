import { create } from 'zustand';
import { RoomState, Round, RoundResult, Player } from '@/types/game';

interface GameStore {
  // Room state
  roomState: RoomState | null;
  isConnected: boolean;
  playerName: string;
  hostToken: string;
  
  // Round state
  currentRound: Round | null;
  speakerEmotion: string | null; // For speaker only
  playerVote: string | null;
  lastResult: RoundResult | null;
  
  // UI state
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setRoomState: (state: RoomState) => void;
  setConnected: (connected: boolean) => void;
  setPlayerName: (name: string) => void;
  setHostToken: (token: string) => void;
  setCurrentRound: (round: Round | null) => void;
  setSpeakerEmotion: (emotion: string | null) => void;
  setPlayerVote: (vote: string | null) => void;
  setLastResult: (result: RoundResult | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const useGameStore = create<GameStore>((set) => ({
  // Initial state
  roomState: null,
  isConnected: false,
  playerName: '',
  hostToken: '',
  currentRound: null,
  speakerEmotion: null,
  playerVote: null,
  lastResult: null,
  isLoading: false,
  error: null,
  
  // Actions
  setRoomState: (state) => set({ roomState: state }),
  setConnected: (connected) => set({ isConnected: connected }),
  setPlayerName: (name) => set({ playerName: name }),
  setHostToken: (token) => set({ hostToken: token }),
  setCurrentRound: (round) => set({ currentRound: round, playerVote: null }),
  setSpeakerEmotion: (emotion) => set({ speakerEmotion: emotion }),
  setPlayerVote: (vote) => set({ playerVote: vote }),
  setLastResult: (result) => set({ lastResult: result }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  reset: () => set({
    roomState: null,
    isConnected: false,
    playerName: '',
    hostToken: '',
    currentRound: null,
    speakerEmotion: null,
    playerVote: null,
    lastResult: null,
    isLoading: false,
    error: null,
  }),
}));