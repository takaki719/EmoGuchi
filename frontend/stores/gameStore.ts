import { create } from 'zustand';
import { RoomState, Round, RoundResult, GameComplete } from '@/types/game';

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
  gameComplete: GameComplete | null;
  
  // Audio state
  audioRecording: Blob | null;
  audioUrl: string | null;
  recordingInProgress: boolean;
  isAudioProcessed: boolean;
  
  // UI state
  isLoading: boolean;
  error: string | null;
  
  // Vote timer state
  voteTimer: {
    startTime: string | null;
    timeoutSeconds: number;
    isActive: boolean;
  };
  
  // Actions
  setRoomState: (state: RoomState) => void;
  setConnected: (connected: boolean) => void;
  setPlayerName: (name: string) => void;
  setHostToken: (token: string) => void;
  setCurrentRound: (round: Round | null) => void;
  setSpeakerEmotion: (emotion: string | null) => void;
  setPlayerVote: (vote: string | null) => void;
  setLastResult: (result: RoundResult | null) => void;
  setGameComplete: (gameComplete: GameComplete | null) => void;
  setAudioRecording: (recording: Blob | null) => void;
  setAudioUrl: (url: string | null) => void;
  setRecordingInProgress: (inProgress: boolean) => void;
  setAudioProcessed: (processed: boolean) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setVoteTimer: (startTime: string | null, timeoutSeconds?: number) => void;
  stopVoteTimer: () => void;
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
  gameComplete: null,
  audioRecording: null,
  audioUrl: null,
  recordingInProgress: false,
  isAudioProcessed: false,
  isLoading: false,
  error: null,
  voteTimer: {
    startTime: null,
    timeoutSeconds: 30,
    isActive: false,
  },
  
  // Actions
  setRoomState: (state) => set({ roomState: state }),
  setConnected: (connected) => set({ isConnected: connected }),
  setPlayerName: (name) => set({ playerName: name }),
  setHostToken: (token) => set({ hostToken: token }),
  setCurrentRound: (round) => set({ currentRound: round, playerVote: null }),
  setSpeakerEmotion: (emotion) => set({ speakerEmotion: emotion }),
  setPlayerVote: (vote) => set({ playerVote: vote }),
  setLastResult: (result) => set({ lastResult: result }),
  setGameComplete: (gameComplete) => set({ gameComplete }),
  setAudioRecording: (recording) => set({ audioRecording: recording }),
  setAudioUrl: (url) => set({ audioUrl: url }),
  setRecordingInProgress: (inProgress) => set({ recordingInProgress: inProgress }),
  setAudioProcessed: (processed) => set({ isAudioProcessed: processed }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  setVoteTimer: (startTime, timeoutSeconds = 30) => set(state => ({
    voteTimer: {
      startTime,
      timeoutSeconds,
      isActive: startTime !== null
    }
  })),
  stopVoteTimer: () => set(state => ({
    voteTimer: {
      ...state.voteTimer,
      isActive: false
    }
  })),
  reset: () => set({
    roomState: null,
    isConnected: false,
    playerName: '',
    hostToken: '',
    currentRound: null,
    speakerEmotion: null,
    playerVote: null,
    lastResult: null,
    gameComplete: null,
    audioRecording: null,
    audioUrl: null,
    recordingInProgress: false,
    isAudioProcessed: false,
    isLoading: false,
    error: null,
    voteTimer: {
      startTime: null,
      timeoutSeconds: 30,
      isActive: false,
    },
  }),
}));