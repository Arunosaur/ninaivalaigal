import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { useState } from "react";
import { Select, type SelectOption } from "./Select";

type OptionValue = "personal" | "work" | "shared" | "archive";

const options: Array<SelectOption<OptionValue>> = [
  { value: "personal", label: "Personal" },
  { value: "work", label: "Work" },
  { value: "shared", label: "Shared" },
  { value: "archive", label: "Archive" }
];

describe("Select", () => {
  it("calls onChange when selecting an option", async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();

    render(<Select<OptionValue> label="Category" value={null} onChange={onChange} options={options} />);

    await user.click(screen.getByRole("button", { name: /category/i }));

    const listbox = await screen.findByRole("listbox");
    await user.click(within(listbox).getByText("Work"));

    expect(onChange).toHaveBeenLastCalledWith("work");
  });

  it("supports multi-select toggling", async () => {
    const user = userEvent.setup();

    function MultiHarness({ onChange }: { onChange: (value: Array<OptionValue>) => void }) {
      const [selected, setSelected] = useState<Array<OptionValue>>(["personal"]);

      return (
        <Select<OptionValue>
          label="Tags"
          value={selected}
          onChange={(next: Array<OptionValue>) => {
            setSelected(next);
            onChange(next);
          }}
          options={options}
          multi
        />
      );
    }

    const onChange = vi.fn();
    render(<MultiHarness onChange={onChange} />);

    await user.click(screen.getByRole("button", { name: /tags/i }));
    const listbox = await screen.findByRole("listbox");
    await user.click(within(listbox).getByText("Work"));
    await user.click(within(listbox).getByText("Personal"));

    expect(onChange.mock.calls[0][0]).toEqual(["personal", "work"]);
    expect(onChange.mock.calls[1][0]).toEqual(["work"]);
  });

  it("filters options when typing in search", async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();

    render(
      <Select<OptionValue>
        label="Filter"
        value={null}
        onChange={onChange}
        options={options}
        searchable
      />
    );

    await user.click(screen.getByRole("button", { name: /filter/i }));
    const searchInput = await screen.findByPlaceholderText(/search/i);

    await user.type(searchInput, "sha");

    expect(await screen.findByText("Shared")).toBeInTheDocument();
    expect(screen.queryByText("Work")).not.toBeInTheDocument();
  });

  it("handles keyboard navigation", async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();

    render(<Select<OptionValue> label="Keyboard" value={null} onChange={onChange} options={options} />);

    const trigger = screen.getByRole("button", { name: /keyboard/i });
    await act(async () => {
      trigger.focus();
    });

    await user.keyboard("{ArrowDown}");
    await user.keyboard("{ArrowDown}");
    await act(async () => {
      await Promise.resolve();
    });
    await user.keyboard("{Enter}");

    expect(onChange).toHaveBeenLastCalledWith("work");
  });
});
