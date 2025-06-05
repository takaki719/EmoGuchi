const EMOTIONS = [
  'Joy',
  'Anticipation',
  'Anger',
  'Disgust',
  'Sadness',
  'Surprise',
  'Fear',
  'Trust',
];

export default function VoteButtons({ onVote }: { onVote: (id: string) => void }) {
  return (
    <div className="grid grid-cols-2 gap-2">
      {EMOTIONS.map((e) => (
        <button
          key={e}
          className="py-2 px-3 bg-blue-600 text-white rounded"
          onClick={() => onVote(e)}
        >
          {e}
        </button>
      ))}
    </div>
  );
}
