export type GameMode = 'basic' | 'advanced' | 'wheel';
export type VoteType = '4choice' | '8choice' | 'wheel';
export type SpeakerOrder = 'random' | 'sequential';
export type GamePhase = 'waiting' | 'in_round' | 'result' | 'closed';

export interface RoomConfig {
  mode: GameMode;
  vote_type: VoteType;
  speaker_order: SpeakerOrder;
  vote_timeout: number;
  max_rounds: number;
}

export interface Player {
  id: string;
  name: string;
  score: number;
  is_host: boolean;
  is_connected: boolean;
}

export interface Room {
  id: string;
  players: { [key: string]: Player };
  config: RoomConfig;
  phase: GamePhase;
  currentSpeaker?: string;
}

export interface RoomState {
  roomId: string;
  players: string[];
  phase: GamePhase;
  config: RoomConfig;
  currentSpeaker?: string;
}

export interface Round {
  id: string;
  phrase: string;
  emotion_id: string;
  speaker_name: string;
  voting_choices?: EmotionChoice[];
  wheel_mode?: boolean;
}

export interface RoundResult {
  round_id: string;
  correct_emotion: string;
  correctEmotionId?: string;
  speaker_name: string;
  scores: { [playerName: string]: number };
  votes: { [playerName: string]: string };
  isGameComplete?: boolean;
  completedRounds?: number;
  maxRounds?: number;
  completedCycles?: number;
  maxCycles?: number;
}

export interface GameComplete {
  rankings: Array<{
    name: string;
    score: number;
    rank: number;
  }>;
  totalRounds: number;
  totalCycles?: number;
}

export interface EmotionChoice {
  id: string;
  name: string;
}

// Socket events
export interface SocketEvents {
  // Client to Server
  join_room: (data: { roomId: string; playerName: string }) => void;
  start_round: (data: {}) => void;
  submit_vote: (data: { roundId: string; emotionId: string }) => void;
  leave_room: (data: {}) => void;
  restart_game: (data: {}) => void;
  audio_send: (data: { audio: ArrayBuffer }) => void;

  // Server to Client
  connected: (data: { message: string }) => void;
  player_joined: (data: { playerName: string; playerId: string }) => void;
  player_reconnected: (data: { playerName: string; playerId: string }) => void;
  player_left: (data: { playerName: string; playerId: string }) => void;
  left_room: (data: { message: string }) => void;
  player_disconnected: (data: { playerName: string; playerId: string }) => void;
  room_state: (data: RoomState) => void;
  round_start: (data: { roundId: string; phrase: string; speakerName: string; votingChoices?: EmotionChoice[] }) => void;
  speaker_emotion: (data: { roundId: string; emotionId: string; emotionName?: string }) => void;
  round_result: (data: RoundResult) => void;
  game_complete: (data: GameComplete) => void;
  audio_received: (data: { audio: ArrayBuffer; speaker_name: string }) => void;
  error: (data: { code: string; message: string }) => void;
}