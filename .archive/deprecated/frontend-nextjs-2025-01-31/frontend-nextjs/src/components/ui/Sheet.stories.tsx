// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import type { Meta, StoryObj } from '@storybook/react';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from './sheet';
import { Button } from './Button';
import { useState } from 'react';

const meta = {
  title: 'UI/Sheet',
  component: Sheet,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Sheet>;

export default meta;
type Story = StoryObj<typeof meta>;

// Basic sheet
export const Basic: Story = {
  render: () => {
    const [open, setOpen] = useState(false);

    return (
      <div className="p-8">
        <Button onClick={() => setOpen(true)}>Open Sheet</Button>
        <Sheet open={open} onOpenChange={setOpen}>
          <SheetContent>
            <SheetHeader>
              <SheetTitle>Sheet Title</SheetTitle>
            </SheetHeader>
            <div className="p-6">
              <p className="text-sm text-secondary-700">
                This is a basic sheet component. Click outside or press ESC to close.
              </p>
            </div>
          </SheetContent>
        </Sheet>
      </div>
    );
  },
};

// Sheet with form
export const WithForm: Story = {
  render: () => {
    const [open, setOpen] = useState(false);

    return (
      <div className="p-8">
        <Button onClick={() => setOpen(true)}>Edit Profile</Button>
        <Sheet open={open} onOpenChange={setOpen}>
          <SheetContent>
            <SheetHeader>
              <SheetTitle>Edit Profile</SheetTitle>
            </SheetHeader>
            <div className="p-6 space-y-4">
              <div>
                <label className="text-sm font-medium text-secondary-900">Name</label>
                <input
                  type="text"
                  className="mt-1 w-full px-3 py-2 border border-secondary-300 rounded-md"
                  placeholder="Your name"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-secondary-900">Email</label>
                <input
                  type="email"
                  className="mt-1 w-full px-3 py-2 border border-secondary-300 rounded-md"
                  placeholder="your@email.com"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-secondary-900">Bio</label>
                <textarea
                  className="mt-1 w-full px-3 py-2 border border-secondary-300 rounded-md"
                  rows={3}
                  placeholder="Tell us about yourself"
                />
              </div>
              <div className="flex gap-2 pt-4">
                <Button variant="secondary" onClick={() => setOpen(false)} fullWidth>
                  Cancel
                </Button>
                <Button onClick={() => setOpen(false)} fullWidth>
                  Save Changes
                </Button>
              </div>
            </div>
          </SheetContent>
        </Sheet>
      </div>
    );
  },
};

// Sheet with list
export const WithList: Story = {
  render: () => {
    const [open, setOpen] = useState(false);

    const notifications = [
      { id: 1, title: 'New message', time: '2 min ago', read: false },
      { id: 2, title: 'Task completed', time: '1 hour ago', read: false },
      { id: 3, title: 'System update', time: '3 hours ago', read: true },
      { id: 4, title: 'New comment', time: '1 day ago', read: true },
    ];

    return (
      <div className="p-8">
        <Button onClick={() => setOpen(true)}>
          View Notifications <span className="ml-2 bg-error-600 text-white rounded-full px-2 py-0.5 text-xs">3</span>
        </Button>
        <Sheet open={open} onOpenChange={setOpen}>
          <SheetContent>
            <SheetHeader>
              <SheetTitle>Notifications</SheetTitle>
            </SheetHeader>
            <div className="divide-y divide-secondary-200">
              {notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`p-4 hover:bg-secondary-50 cursor-pointer ${
                    !notification.read ? 'bg-primary-50' : ''
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm font-medium text-secondary-900">
                        {notification.title}
                      </p>
                      <p className="text-xs text-secondary-600 mt-1">{notification.time}</p>
                    </div>
                    {!notification.read && (
                      <div className="w-2 h-2 bg-primary-600 rounded-full" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          </SheetContent>
        </Sheet>
      </div>
    );
  },
};

// Sheet with scrollable content
export const WithScrollableContent: Story = {
  render: () => {
    const [open, setOpen] = useState(false);

    return (
      <div className="p-8">
        <Button onClick={() => setOpen(true)}>View Long Content</Button>
        <Sheet open={open} onOpenChange={setOpen}>
          <SheetContent>
            <SheetHeader>
              <SheetTitle>Terms and Conditions</SheetTitle>
            </SheetHeader>
            <div className="p-6 space-y-4 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 100px)' }}>
              {Array.from({ length: 20 }).map((_, i) => (
                <p key={i} className="text-sm text-secondary-700">
                  Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod
                  tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam,
                  quis nostrud exercitation ullamco laboris.
                </p>
              ))}
              <div className="pt-4">
                <Button onClick={() => setOpen(false)} fullWidth>
                  Accept
                </Button>
              </div>
            </div>
          </SheetContent>
        </Sheet>
      </div>
    );
  },
};

// Sheet with actions
export const WithActions: Story = {
  render: () => {
    const [open, setOpen] = useState(false);

    return (
      <div className="p-8">
        <Button variant="destructive" onClick={() => setOpen(true)}>
          Delete Item
        </Button>
        <Sheet open={open} onOpenChange={setOpen}>
          <SheetContent>
            <SheetHeader>
              <SheetTitle>Confirm Deletion</SheetTitle>
            </SheetHeader>
            <div className="p-6 space-y-4">
              <p className="text-sm text-secondary-700">
                Are you sure you want to delete this item? This action cannot be undone.
              </p>
              <div className="bg-error-50 border border-error-200 rounded-md p-3">
                <p className="text-sm text-error-800">
                  ⚠️ Warning: This will permanently delete all associated data.
                </p>
              </div>
              <div className="flex gap-2 pt-4">
                <Button variant="secondary" onClick={() => setOpen(false)} fullWidth>
                  Cancel
                </Button>
                <Button variant="destructive" onClick={() => setOpen(false)} fullWidth>
                  Delete
                </Button>
              </div>
            </div>
          </SheetContent>
        </Sheet>
      </div>
    );
  },
};
