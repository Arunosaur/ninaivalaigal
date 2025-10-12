import type { Meta, StoryObj } from "@storybook/react";
import { useState } from "react";
import { Textarea } from "./Textarea";

const meta: Meta<typeof Textarea> = {
  title: "Components/Textarea",
  component: Textarea,
  args: {
    label: "Description",
    placeholder: "Share more about this memory",
    helperText: "Markdown is supported"
  }
};

export default meta;

type Story = StoryObj<typeof Textarea>;

export const Default: Story = {
  render: (args) => {
    const [value, setValue] = useState<string>("");

    return (
      <Textarea
        {...args}
        value={value}
        onChange={(event) => setValue(event.target.value)}
        maxLength={240}
      />
    );
  }
};

export const WithError: Story = {
  render: (args) => (
    <Textarea
      {...args}
      label="Summary"
      helperText="Provide a short summary"
      errorText="Summary cannot be empty"
      maxLength={160}
    />
  )
};

export const AutoResize: Story = {
  render: (args) => {
    const [value, setValue] = useState(
      "This textarea grows with its content. Start typing to see the height adjust automatically."
    );

    return (
      <Textarea
        {...args}
        label="Auto-resizing notes"
        value={value}
        onChange={(event) => setValue(event.target.value)}
        autoResize
        helperText="Height adapts to your content"
        maxLength={500}
      />
    );
  }
};

export const WithHelperOnly: Story = {
  render: (args) => (
    <Textarea
      {...args}
      label="Internal notes"
      helperText="Visible only to admins"
      placeholder="Add additional context for the ops team"
    />
  )
};
