export interface Player {
  id: string;
  name: string;
}

export interface RoomState {
  roomId: string;
  players: Player[];
  phrase?: string;
  roundId?: string;
  scores?: Record<string, number>;
}
