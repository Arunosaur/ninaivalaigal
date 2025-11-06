// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useRef, useState } from "react";
import { describe, expect, it, vi } from "vitest";
import { Button } from "./Button";
import { Modal } from "./Modal";

describe("Modal", () => {
  it("renders children when open and wires accessibility attributes", () => {
    const onClose = vi.fn();

    render(
      <Modal isOpen onClose={onClose} data-testid="modal">
        <Modal.Header>
          <div>
            <Modal.Title>Session details</Modal.Title>
            <Modal.Description>We will cover AI summaries and timelines.</Modal.Description>
          </div>
          <Modal.CloseButton />
        </Modal.Header>
        <Modal.Body>
          <p>Today&apos;s review covers memory snapshots and AI tasks.</p>
        </Modal.Body>
      </Modal>
    );

    const dialog = screen.getByRole("dialog", { name: /session details/i });
    expect(dialog).toBeInTheDocument();
    expect(dialog).toHaveAttribute("aria-describedby");
  });

  it("invokes onClose when clicking the overlay or pressing Escape", async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();

    render(
      <Modal isOpen onClose={onClose}>
        <Modal.Header>
          <Modal.Title>Overlay test</Modal.Title>
          <Modal.CloseButton />
        </Modal.Header>
        <Modal.Body>
          <p>Testing close handling.</p>
        </Modal.Body>
      </Modal>
    );

    const overlay = screen.getByTestId("modal-overlay");
    await user.click(overlay);
    expect(onClose).toHaveBeenCalledTimes(1);

    await user.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalledTimes(2);
  });

  it("traps focus within the modal and restores focus on close", async () => {
    const user = userEvent.setup();

    function TestHarness() {
      const [isOpen, setIsOpen] = useState(false);
      const confirmRef = useRef<HTMLButtonElement | null>(null);

      return (
        <div>
          <Button onClick={() => setIsOpen(true)}>Launch modal</Button>
          <Modal isOpen={isOpen} onClose={() => setIsOpen(false)} initialFocusRef={confirmRef}>
            <Modal.Header>
              <Modal.Title>Focus handling</Modal.Title>
              <Modal.CloseButton data-testid="close-button" />
            </Modal.Header>
            <Modal.Body>
              <p>Ensure focus stays inside dialog.</p>
            </Modal.Body>
            <Modal.Footer>
              <Button ref={confirmRef}>Confirm</Button>
              <Button>Secondary</Button>
            </Modal.Footer>
          </Modal>
        </div>
      );
    }

    render(<TestHarness />);

    await user.tab();
    const launchButton = screen.getByRole("button", { name: /launch modal/i });
    expect(launchButton).toHaveFocus();

    await act(async () => {
      await user.click(launchButton);
    });

    const dialog = await screen.findByRole("dialog", { name: /focus handling/i });
    const confirmButton = await screen.findByRole("button", { name: /confirm/i });
    expect(confirmButton).toHaveFocus();

    for (let i = 0; i < 4; i += 1) {
      await user.tab();
      expect(dialog.contains(document.activeElement)).toBe(true);
    }

    await act(async () => {
      await user.keyboard("{Escape}");
    });
    expect(launchButton).toHaveFocus();
  });
});
