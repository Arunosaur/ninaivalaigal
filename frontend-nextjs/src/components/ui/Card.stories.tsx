import type { Meta, StoryObj } from '@storybook/react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from './card';
import { Button } from './Button';

const meta = {
  title: 'UI/Card',
  component: Card,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Card>;

export default meta;
type Story = StoryObj<typeof meta>;

// Basic card
export const Basic: Story = {
  render: () => (
    <Card className="w-[350px]">
      <CardContent className="pt-6">
        <p>This is a basic card with content.</p>
      </CardContent>
    </Card>
  ),
};

// Card with header
export const WithHeader: Story = {
  render: () => (
    <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Card Title</CardTitle>
        <CardDescription>Card description goes here</CardDescription>
      </CardHeader>
      <CardContent>
        <p>This card has a header with title and description.</p>
      </CardContent>
    </Card>
  ),
};

// Card with footer
export const WithFooter: Story = {
  render: () => (
    <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Confirm Action</CardTitle>
        <CardDescription>Are you sure you want to continue?</CardDescription>
      </CardHeader>
      <CardContent>
        <p>This action cannot be undone.</p>
      </CardContent>
      <CardFooter className="flex justify-end gap-2">
        <Button variant="secondary" size="sm">Cancel</Button>
        <Button size="sm">Confirm</Button>
      </CardFooter>
    </Card>
  ),
};

// Complete card
export const Complete: Story = {
  render: () => (
    <Card className="w-[380px]">
      <CardHeader>
        <CardTitle>Project Update</CardTitle>
        <CardDescription>Important changes to review</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <p className="text-sm text-secondary-700">
            Your project has been successfully updated with the latest changes.
            All team members have been notified.
          </p>
          <div className="flex items-center gap-2 text-xs text-secondary-600">
            <span>Last updated: 2 minutes ago</span>
          </div>
        </div>
      </CardContent>
      <CardFooter className="flex justify-between">
        <Button variant="ghost" size="sm">Learn More</Button>
        <Button size="sm">View Details</Button>
      </CardFooter>
    </Card>
  ),
};

// Interactive card example
export const InteractiveCard: Story = {
  render: () => (
    <Card className="w-[380px] hover:shadow-md transition-shadow cursor-pointer">
      <CardHeader>
        <CardTitle>Memory Card</CardTitle>
        <CardDescription>Click to expand</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm">
          This is an interactive card that responds to hover states.
        </p>
      </CardContent>
    </Card>
  ),
};

// Multiple cards layout
export const MultipleCards: Story = {
  render: () => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4">
      <Card>
        <CardHeader>
          <CardTitle>Card 1</CardTitle>
          <CardDescription>First card</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm">Content for the first card.</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Card 2</CardTitle>
          <CardDescription>Second card</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm">Content for the second card.</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Card 3</CardTitle>
          <CardDescription>Third card</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm">Content for the third card.</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Card 4</CardTitle>
          <CardDescription>Fourth card</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm">Content for the fourth card.</p>
        </CardContent>
      </Card>
    </div>
  ),
  parameters: {
    layout: 'fullscreen',
  },
};

// Card with custom styling
export const CustomStyling: Story = {
  render: () => (
    <Card className="w-[350px] bg-primary-50 border-primary-200">
      <CardHeader>
        <CardTitle className="text-primary-900">Custom Styled Card</CardTitle>
        <CardDescription className="text-primary-700">
          This card uses custom colors
        </CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-primary-800">
          You can customize card styling with Tailwind classes.
        </p>
      </CardContent>
    </Card>
  ),
};
