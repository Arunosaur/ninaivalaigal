'use client';

import { useState } from 'react';
import { Modal, Button, Input } from '@ninaivalaigal/ui-components';
import { useMemories } from '../hooks/useMemories';

interface CreateMemoryModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function CreateMemoryModal({ isOpen, onClose }: CreateMemoryModalProps) {
  const { createMemory } = useMemories();

  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [category, setCategory] = useState<'personal' | 'work' | 'shared'>('personal');
  const [tags, setTags] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    const tagArray = tags
      .split(',')
      .map(tag => tag.trim())
      .filter(tag => tag.length > 0);

    const { memory, error: createError } = await createMemory({
      title: title || undefined,
      content,
      category,
      tags: tagArray.length > 0 ? tagArray : undefined,
    });

    setIsLoading(false);

    if (createError) {
      setError(createError);
    } else if (memory) {
      // Success - reset form and close
      setTitle('');
      setContent('');
      setCategory('personal');
      setTags('');
      onClose();
    }
  };

  const handleClose = () => {
    if (!isLoading) {
      setTitle('');
      setContent('');
      setCategory('personal');
      setTags('');
      setError(null);
      onClose();
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="lg">
      <Modal.Header>
        <Modal.Title>Create New Memory</Modal.Title>
        <Modal.CloseButton />
      </Modal.Header>

      <form onSubmit={handleSubmit}>
        <Modal.Body>
          <div className="space-y-4">
            {/* Title Input */}
            <div>
              <label htmlFor="memory-title" className="block text-sm font-medium text-gray-700">
                Title <span className="text-gray-400">(optional)</span>
              </label>
              <Input
                id="memory-title"
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Give your memory a title..."
                className="mt-1"
                disabled={isLoading}
              />
            </div>

            {/* Content Textarea - Placeholder until Textarea component ready */}
            <div>
              <label htmlFor="memory-content" className="block text-sm font-medium text-gray-700">
                Content <span className="text-red-500">*</span>
              </label>
              <textarea
                id="memory-content"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Write your memory here..."
                rows={6}
                required
                disabled={isLoading}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-50 disabled:text-gray-500"
              />
              <p className="mt-1 text-xs text-gray-500">
                {content.length} characters
              </p>
            </div>

            {/* Category Select - Placeholder until Select component ready */}
            <div>
              <label htmlFor="memory-category" className="block text-sm font-medium text-gray-700">
                Category
              </label>
              <select
                id="memory-category"
                value={category}
                onChange={(e) => setCategory(e.target.value as 'personal' | 'work' | 'shared')}
                disabled={isLoading}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-50 disabled:text-gray-500"
              >
                <option value="personal">Personal</option>
                <option value="work">Work</option>
                <option value="shared">Shared</option>
              </select>
            </div>

            {/* Tags Input */}
            <div>
              <label htmlFor="memory-tags" className="block text-sm font-medium text-gray-700">
                Tags <span className="text-gray-400">(optional)</span>
              </label>
              <Input
                id="memory-tags"
                type="text"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                placeholder="meetings, planning, ideas (comma-separated)"
                className="mt-1"
                disabled={isLoading}
              />
              <p className="mt-1 text-xs text-gray-500">
                Separate tags with commas
              </p>
            </div>

            {/* Error Display */}
            {error && (
              <div className="rounded-md bg-red-50 p-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}
          </div>
        </Modal.Body>

        <Modal.Footer>
          <Button
            type="button"
            variant="secondary"
            onClick={handleClose}
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            isLoading={isLoading}
            disabled={!content.trim()}
          >
            Create Memory
          </Button>
        </Modal.Footer>
      </form>
    </Modal>
  );
}
