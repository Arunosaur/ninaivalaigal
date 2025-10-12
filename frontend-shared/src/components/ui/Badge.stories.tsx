// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import type { Meta, StoryObj } from "@storybook/react";
import { Badge } from "./Badge";

const meta: Meta<typeof Badge> = {
  title: "Components/Badge",
  component: Badge,
  args: {
    children: "Badge",
    variant: "neutral"
  }
};

export default meta;

type Story = StoryObj<typeof Badge>;

export const Playground: Story = {};

export const Variants: Story = {
  render: () => (
    <div className="flex flex-wrap gap-2">
      <Badge variant="neutral">Neutral</Badge>
      <Badge variant="primary">Primary</Badge>
      <Badge variant="info">Info</Badge>
      <Badge variant="accent">Accent</Badge>
      <Badge variant="success">Success</Badge>
      <Badge variant="warning">Warning</Badge>
      <Badge variant="danger">Danger</Badge>
    </div>
  )
};

export const PillBadges: Story = {
  render: () => (
    <div className="flex flex-wrap gap-2">
      <Badge pill>Default</Badge>
      <Badge variant="info" pill>
        Personal
      </Badge>
      <Badge variant="accent" pill>
        Work
      </Badge>
      <Badge variant="success" pill>
        Shared
      </Badge>
    </div>
  )
};

export const WithIcon: Story = {
  render: () => (
    <Badge variant="info" pill>
      <span className="inline-block h-2 w-2 rounded-full bg-blue-500" aria-hidden />
      Synced
    </Badge>
  )
};
