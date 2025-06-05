import { useRoomStore } from '../stores/useRoomStore';
import PlayerList from './PlayerList';

export default function Lobby() {
  const players = useRoomStore((s) => s.players);
  return (
    <div className="p-4 space-y-4">
      <h1 className="text-xl font-bold">Lobby</h1>
      <PlayerList players={players} />
    </div>
  );
}
