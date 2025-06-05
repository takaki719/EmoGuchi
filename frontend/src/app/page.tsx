'use client';
import Lobby from '../components/Lobby';
import VoteButtons from '../components/VoteButtons';
import Results from '../components/Results';
import { useRoomStore } from '../stores/useRoomStore';
import { useSocket } from '../hooks/useSocket';
import { submitVote } from '../socket';

export default function Home() {
  const room = useRoomStore((s) => s.room);
  useSocket(room?.roomId, 'demo');

  return (
    <main className="p-4 space-y-6">
      <Lobby />
      {room?.phrase && (
        <div className="space-y-4">
          <p className="text-lg font-medium">{room.phrase}</p>
          <VoteButtons onVote={(id) => submitVote(room.roundId || '', id)} />
        </div>
      )}
      {room && <Results room={room} />}
    </main>
  );
}
