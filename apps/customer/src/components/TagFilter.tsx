// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * US#338: Tag Filter UI Component (SPEC-034)
 *
 * Hierarchical tag filtering component for memory browser.
 * Supports tag selection, multi-select, and hierarchical organization.
 */

import { useState } from 'react';

export interface Tag {
  id: string;
  name: string;
  parent_id: string | null;
  count?: number;
}

interface TagFilterProps {
  tags: Tag[];
  selectedTags: string[];
  onTagsChange: (tagIds: string[]) => void;
  className?: string;
}

export function TagFilter({ tags, selectedTags, onTagsChange, className = '' }: TagFilterProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedParents, setExpandedParents] = useState<Set<string>>(new Set());

  // Build hierarchical structure
  const rootTags = tags.filter((tag) => !tag.parent_id);
  const childTagsByParent = new Map<string, Tag[]>();
  tags.forEach((tag) => {
    if (tag.parent_id) {
      const children = childTagsByParent.get(tag.parent_id) || [];
      children.push(tag);
      childTagsByParent.set(tag.parent_id, children);
    }
  });

  // Filter tags by search term
  const filteredTags = tags.filter(
    (tag) => tag.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Filter root tags for display
  const displayRootTags = searchTerm
    ? filteredTags.filter((tag) => !tag.parent_id)
    : rootTags;

  const toggleTag = (tagId: string) => {
    if (selectedTags.includes(tagId)) {
      onTagsChange(selectedTags.filter((id) => id !== tagId));
    } else {
      onTagsChange([...selectedTags, tagId]);
    }
  };

  const toggleParent = (parentId: string) => {
    const newExpanded = new Set(expandedParents);
    if (newExpanded.has(parentId)) {
      newExpanded.delete(parentId);
    } else {
      newExpanded.add(parentId);
    }
    setExpandedParents(newExpanded);
  };

  const clearAll = () => {
    onTagsChange([]);
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Search */}
      <div className="relative">
        <input
          type="text"
          placeholder="Search tags..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
        />
        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400">🔍</span>
      </div>

      {/* Selected Tags Count */}
      {selectedTags.length > 0 && (
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-400">
            {selectedTags.length} tag{selectedTags.length !== 1 ? 's' : ''} selected
          </span>
          <button
            onClick={clearAll}
            className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors duration-300"
          >
            Clear all
          </button>
        </div>
      )}

      {/* Tag List */}
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {displayRootTags.length === 0 ? (
          <div className="text-center py-8 text-slate-400">
            <p className="text-sm">No tags found</p>
          </div>
        ) : (
          displayRootTags.map((tag) => {
            const children = childTagsByParent.get(tag.id) || [];
            const isExpanded = expandedParents.has(tag.id);
            const isSelected = selectedTags.includes(tag.id);
            const hasSelectedChildren =
              children.length > 0 &&
              children.some((child) => selectedTags.includes(child.id));

            return (
              <div key={tag.id} className="space-y-1">
                {/* Parent Tag */}
                <div className="flex items-center space-x-2">
                  {children.length > 0 && (
                    <button
                      onClick={() => toggleParent(tag.id)}
                      className="text-slate-400 hover:text-white transition-colors duration-300"
                    >
                      {isExpanded ? '▼' : '▶'}
                    </button>
                  )}
                  <label className="flex items-center space-x-2 flex-1 cursor-pointer group">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => toggleTag(tag.id)}
                      className="w-4 h-4 rounded border-white/20 bg-slate-900/70 text-indigo-600 focus:ring-indigo-500 focus:ring-2"
                    />
                    <span
                      className={`
                        text-sm transition-colors duration-300
                        ${isSelected || hasSelectedChildren
                          ? 'text-white font-medium'
                          : 'text-slate-300 group-hover:text-white'
                        }
                      `}
                    >
                      {tag.name}
                    </span>
                    {tag.count !== undefined && (
                      <span className="text-xs text-slate-500">({tag.count})</span>
                    )}
                  </label>
                </div>

                {/* Children Tags */}
                {isExpanded && children.length > 0 && (
                  <div className="ml-6 space-y-1">
                    {children.map((child) => {
                      const isChildSelected = selectedTags.includes(child.id);
                      return (
                        <label
                          key={child.id}
                          className="flex items-center space-x-2 cursor-pointer group"
                        >
                          <input
                            type="checkbox"
                            checked={isChildSelected}
                            onChange={() => toggleTag(child.id)}
                            className="w-4 h-4 rounded border-white/20 bg-slate-900/70 text-indigo-600 focus:ring-indigo-500 focus:ring-2"
                          />
                          <span
                            className={`
                              text-sm transition-colors duration-300
                              ${isChildSelected
                                ? 'text-white font-medium'
                                : 'text-slate-400 group-hover:text-slate-300'
                              }
                            `}
                          >
                            {child.name}
                          </span>
                          {child.count !== undefined && (
                            <span className="text-xs text-slate-500">({child.count})</span>
                          )}
                        </label>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
