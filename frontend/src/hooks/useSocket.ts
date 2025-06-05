import { useEffect } from 'react';
import { connect, disconnect, onPlayerJoined, onRoundStart, onRoundResult } from '../socket';
import { useRoomStore } from '../stores/useRoomStore';

export function useSocket(roomId?: string, playerName?: string) {
  const addPlayer = useRoomStore((s) => s.addPlayer);
  const setRoom = useRoomStore((s) => s.setRoom);

  useEffect(() => {
    if (!roomId || !playerName) return;
    connect(roomId, playerName);
    onPlayerJoined(addPlayer);
    onRoundStart((payload) =>
      setRoom({ roomId, players: [], phrase: payload.phrase, roundId: payload.roundId })
    );
    onRoundResult((payload) =>
      setRoom({ roomId, players: [], scores: payload.scores })
    );
    return () => disconnect();
  }, [roomId, playerName, addPlayer, setRoom]);
}
