import type { Player } from '../types';

export default function PlayerList({ players }: { players: Player[] }) {
  return (
    <ul className="space-y-1">
      {players.map((p) => (
        <li key={p.id} className="p-2 bg-gray-100 rounded">
          {p.name}
        </li>
      ))}
    </ul>
  );
}
