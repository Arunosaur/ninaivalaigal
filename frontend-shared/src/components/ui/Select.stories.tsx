import type { Meta, StoryObj } from "@storybook/react";
import { useState } from "react";
import { Select, type SelectOption } from "./Select";

type OptionValue = "personal" | "work" | "shared" | "archive" | "favorites";

const baseOptions: Array<SelectOption<OptionValue>> = [
  { value: "personal", label: "Personal", description: "Private notes and memories" },
  { value: "work", label: "Work", description: "Team initiatives and meeting notes" },
  { value: "shared", label: "Shared", description: "Collaborative spaces" },
  { value: "archive", label: "Archive", description: "Cold storage" },
  { value: "favorites", label: "Favorites", description: "Quick access items" }
];

const meta: Meta<typeof Select<OptionValue>> = {
  title: "Components/Select",
  component: Select,
  args: {
    options: baseOptions,
    label: "Memory category",
    helperText: "Choose where this memory should live"
  }
};

export default meta;

type Story = StoryObj<typeof Select<OptionValue>>;

export const Default: Story = {
  render: (args) => {
    const [value, setValue] = useState<OptionValue | null>("personal");

    return (
      <div className="max-w-sm space-y-4">
        <Select<OptionValue> {...args} value={value} onChange={setValue} />
        <div className="text-sm text-slate-500 dark:text-slate-300">Selected: {value ?? "None"}</div>
      </div>
    );
  }
};

export const Searchable: Story = {
  render: (args) => {
    const [value, setValue] = useState<OptionValue | null>(null);

    return (
      <Select<OptionValue>
        {...args}
        placeholder="Search categories"
        value={value}
        onChange={setValue}
        searchable
        helperText="Start typing to filter categories"
      />
    );
  }
};

export const MultiSelect: Story = {
  render: (args) => {
    const [value, setValue] = useState<Array<OptionValue>>(["personal", "work"]);

    return (
      <Select<OptionValue>
        {...args}
        value={value}
        onChange={setValue}
        multi
        placeholder="Select tags"
        helperText="You can choose multiple collections"
      />
    );
  }
};

export const ErrorState: Story = {
  render: (args) => {
    const [value, setValue] = useState<OptionValue | null>(null);

    return (
      <Select<OptionValue>
        {...args}
        value={value}
        onChange={setValue}
        error={value ? false : "Category is required"}
        placeholder="Pick a category"
      />
    );
  }
};

export const NativeVariant: Story = {
  render: (args) => {
    const [value, setValue] = useState<OptionValue | null>("shared");

    return (
      <Select<OptionValue>
        {...args}
        variant="native"
        value={value}
        onChange={setValue}
        helperText="Native select is accessible everywhere"
      />
    );
  }
};
