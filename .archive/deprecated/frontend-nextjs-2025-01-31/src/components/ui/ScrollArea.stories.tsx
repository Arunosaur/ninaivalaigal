// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import type { Meta, StoryObj } from '@storybook/react';
import { ScrollArea } from './scroll-area';

const meta = {
  title: 'UI/ScrollArea',
  component: ScrollArea,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof ScrollArea>;

export default meta;
type Story = StoryObj<typeof meta>;

// Basic scroll area
export const Basic: Story = {
  render: () => (
    <ScrollArea className="h-[200px] w-[300px] border border-secondary-200 rounded-md p-4">
      <div className="space-y-2">
        {Array.from({ length: 20 }).map((_, i) => (
          <p key={i} className="text-sm text-secondary-700">
            Item {i + 1}
          </p>
        ))}
      </div>
    </ScrollArea>
  ),
};

// With long content
export const LongContent: Story = {
  render: () => (
    <ScrollArea className="h-[300px] w-[400px] border border-secondary-200 rounded-md p-4">
      <div className="space-y-4">
        <h3 className="font-semibold text-secondary-900">Long Article</h3>
        {Array.from({ length: 10 }).map((_, i) => (
          <p key={i} className="text-sm text-secondary-700">
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod
            tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam,
            quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo
            consequat.
          </p>
        ))}
      </div>
    </ScrollArea>
  ),
};

// Horizontal scroll
export const HorizontalScroll: Story = {
  render: () => (
    <ScrollArea className="w-[300px] border border-secondary-200 rounded-md p-4">
      <div className="flex gap-4" style={{ width: '800px' }}>
        {Array.from({ length: 10 }).map((_, i) => (
          <div
            key={i}
            className="flex-shrink-0 w-24 h-24 bg-primary-100 rounded-md flex items-center justify-center"
          >
            <span className="text-sm font-medium text-primary-900">{i + 1}</span>
          </div>
        ))}
      </div>
    </ScrollArea>
  ),
};

// List with scroll
export const ListWithScroll: Story = {
  render: () => (
    <ScrollArea className="h-[250px] w-[350px] border border-secondary-200 rounded-md">
      <div className="divide-y divide-secondary-200">
        {Array.from({ length: 15 }).map((_, i) => (
          <div key={i} className="p-4 hover:bg-secondary-50">
            <h4 className="font-medium text-secondary-900">List Item {i + 1}</h4>
            <p className="text-sm text-secondary-600">Description for item {i + 1}</p>
          </div>
        ))}
      </div>
    </ScrollArea>
  ),
};

// Chat messages
export const ChatMessages: Story = {
  render: () => (
    <ScrollArea className="h-[400px] w-[350px] border border-secondary-200 rounded-md p-4">
      <div className="space-y-4">
        {Array.from({ length: 10 }).map((_, i) => {
          const isUser = i % 2 === 0;
          return (
            <div key={i} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[70%] rounded-lg p-3 ${
                  isUser
                    ? 'bg-primary-600 text-white'
                    : 'bg-secondary-100 text-secondary-900'
                }`}
              >
                <p className="text-sm">
                  {isUser ? 'User message' : 'Bot response'} {i + 1}
                </p>
                <p className="text-xs mt-1 opacity-75">
                  {new Date().toLocaleTimeString()}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </ScrollArea>
  ),
};

// Grid with scroll
export const GridWithScroll: Story = {
  render: () => (
    <ScrollArea className="h-[350px] w-[400px] border border-secondary-200 rounded-md p-4">
      <div className="grid grid-cols-3 gap-4">
        {Array.from({ length: 24 }).map((_, i) => (
          <div
            key={i}
            className="aspect-square bg-secondary-100 rounded-md flex items-center justify-center hover:bg-secondary-200 cursor-pointer"
          >
            <span className="text-sm font-medium text-secondary-900">{i + 1}</span>
          </div>
        ))}
      </div>
    </ScrollArea>
  ),
};

// Code block
export const CodeBlock: Story = {
  render: () => (
    <ScrollArea className="h-[300px] w-[500px] border border-secondary-200 rounded-md p-4 bg-secondary-900">
      <pre className="text-xs text-secondary-100">
        <code>{`// Example code with long lines
function exampleFunction(param1, param2, param3, param4, param5) {
  const result = param1 + param2 + param3 + param4 + param5;
  console.log('This is a very long line that will require horizontal scrolling to see completely');

  if (result > 100) {
    return 'Result is greater than 100';
  } else {
    return 'Result is less than or equal to 100';
  }
}

// More code lines
${Array.from({ length: 20 })
  .map((_, i) => `const variable${i} = ${i * 10};`)
  .join('\n')}
        `}</code>
      </pre>
    </ScrollArea>
  ),
};
