import { Card } from '@ninaivalaigal/ui-components';

export type Memory = {
  id: string;
  title: string;
  content: string;
  category: 'personal' | 'work' | 'shared';
  createdAt: string;
  tags?: string[];
};

type MemoryCardProps = {
  memory: Memory;
  onClick?: (memory: Memory) => void;
};

export function MemoryCard({ memory, onClick }: MemoryCardProps) {
  const categoryColors = {
    personal: 'bg-blue-100 text-blue-800',
    work: 'bg-purple-100 text-purple-800',
    shared: 'bg-green-100 text-green-800',
  };

  const handleClick = () => {
    onClick?.(memory);
  };

  return (
    <Card
      className="cursor-pointer bg-white transition-shadow hover:shadow-lg"
      onClick={handleClick}
    >
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-start justify-between">
          <h3 className="line-clamp-2 text-lg font-semibold text-gray-900">
            {memory.title}
          </h3>
          <span
            className={`ml-2 flex-shrink-0 rounded-full px-2 py-1 text-xs font-medium ${
              categoryColors[memory.category]
            }`}
          >
            {memory.category}
          </span>
        </div>

        {/* Content Preview */}
        <p className="line-clamp-3 text-sm text-gray-600">{memory.content}</p>

        {/* Tags */}
        {memory.tags && memory.tags.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {memory.tags.slice(0, 3).map((tag) => (
              <span
                key={tag}
                className="rounded-md bg-gray-100 px-2 py-1 text-xs text-gray-700"
              >
                #{tag}
              </span>
            ))}
            {memory.tags.length > 3 && (
              <span className="rounded-md bg-gray-100 px-2 py-1 text-xs text-gray-700">
                +{memory.tags.length - 3}
              </span>
            )}
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-gray-100 pt-3 text-xs text-gray-500">
          <span>{new Date(memory.createdAt).toLocaleDateString()}</span>
          <div className="flex items-center space-x-2">
            <button
              className="text-gray-400 hover:text-gray-600"
              onClick={(e) => {
                e.stopPropagation();
                console.log('Share memory:', memory.id);
              }}
            >
              <svg
                className="h-4 w-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"
                />
              </svg>
            </button>
            <button
              className="text-gray-400 hover:text-gray-600"
              onClick={(e) => {
                e.stopPropagation();
                console.log('Edit memory:', memory.id);
              }}
            >
              <svg
                className="h-4 w-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </Card>
  );
}
