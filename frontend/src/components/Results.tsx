import type { RoomState } from '../types';

export default function Results({ room }: { room: RoomState }) {
  if (!room.scores) return null;
  return (
    <div className="mt-4">
      <h2 className="font-bold mb-2">Results</h2>
      <ul>
        {Object.entries(room.scores).map(([player, score]) => (
          <li key={player}>{player}: {score}</li>
        ))}
      </ul>
    </div>
  );
}
