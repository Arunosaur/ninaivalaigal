import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { Textarea } from "./Textarea";

describe("Textarea", () => {
  it("renders label, helper text, and character count", () => {
    render(
      <Textarea
        label="Description"
        helperText="Share the details"
        maxLength={120}
        defaultValue="Hello"
      />
    );

    expect(screen.getByLabelText("Description")).toBeInTheDocument();
    expect(screen.getByText("Share the details")).toBeInTheDocument();
    expect(screen.getByText("5 / 120")).toBeInTheDocument();
  });

  it("updates character count when typing", async () => {
    const user = userEvent.setup();

    render(<Textarea label="Notes" maxLength={10} />);

    const textarea = screen.getByLabelText("Notes");
    await act(async () => {
      await user.type(textarea, "memory");
    });

    expect(screen.getByText("6 / 10")).toBeInTheDocument();
  });

  it("prefers showing error text when provided", () => {
    render(
      <Textarea
        label="Summary"
        helperText="This will be shared with your team"
        errorText="Summary is required"
      />
    );

    expect(screen.getByText("Summary is required")).toBeInTheDocument();
    expect(screen.queryByText("This will be shared with your team")).not.toBeInTheDocument();
  });

  it("auto-resizes when enabled", async () => {
    const user = userEvent.setup();

    render(<Textarea label="Auto" autoResize />);

    const textarea = screen.getByLabelText("Auto");
    Object.defineProperty(textarea, "scrollHeight", {
      configurable: true,
      value: 180
    });

    await act(async () => {
      await user.type(textarea, "resize");
    });

    expect(textarea.style.height).toBe("180px");
  });

  it("wires helper text and counter to aria-describedby", () => {
    render(
      <Textarea
        label="Summary"
        helperText="Visible to all team members"
        maxLength={12}
        defaultValue="ready"
      />
    );

    const textarea = screen.getByLabelText("Summary");
    const helper = screen.getByText("Visible to all team members");
    const counter = screen.getByText("5 / 12");

    expect(textarea).toHaveAttribute("aria-describedby", `${helper.id} ${counter.id}`);
  });
});
