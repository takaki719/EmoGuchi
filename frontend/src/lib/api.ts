const BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL;

export interface CreateRoomParams {
  mode?: string;
  voteType?: string;
  speakerOrder?: string;
}

export async function createRoom(params: CreateRoomParams) {
  const res = await fetch(`${BASE_URL}/api/v1/rooms`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error('Failed to create room');
  return res.json();
}

export async function getRoom(roomId: string) {
  const res = await fetch(`${BASE_URL}/api/v1/rooms/${roomId}`);
  if (!res.ok) throw new Error('Failed to fetch room');
  return res.json();
}

export async function prefetchPhrases(roomId: string) {
  const res = await fetch(`${BASE_URL}/api/v1/rooms/${roomId}/prefetch`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to prefetch');
  return res.json();
}
