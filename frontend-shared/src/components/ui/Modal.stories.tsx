// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import type { Meta, StoryObj } from "@storybook/react";
import { useRef, useState } from "react";
import { Button } from "./Button";
import { Modal } from "./Modal";

const meta: Meta<typeof Modal> = {
  title: "Components/Modal",
  component: Modal,
  parameters: {
    layout: "centered"
  },
  args: {
    size: "md",
    align: "center"
  }
};

export default meta;

type Story = StoryObj<typeof Modal>;

function ExampleModalContent({ onClose }: { onClose: () => void }) {
  const confirmButtonRef = useRef<HTMLButtonElement | null>(null);

  return (
    <Modal isOpen onClose={onClose} initialFocusRef={confirmButtonRef}>
      <Modal.Header>
        <div>
          <Modal.Title>Upgrade Your Memory Plan</Modal.Title>
          <Modal.Description>
            Unlock unlimited daily memory captures, collaborative workspaces, and premium AI assistance.
          </Modal.Description>
        </div>
        <Modal.CloseButton />
      </Modal.Header>
      <Modal.Body>
        <p>
          Switching to the Pro plan immediately grants enhanced analytics, timeline history, and automated summarization.
          You can downgrade at any time directly from the billing portal.
        </p>
      </Modal.Body>
      <Modal.Footer>
        <Button ref={confirmButtonRef} onClick={onClose} variant="primary">
          Confirm upgrade
        </Button>
        <Button onClick={onClose} variant="secondary">
          Cancel
        </Button>
      </Modal.Footer>
    </Modal>
  );
}

export const Playground: Story = {
  render: (args) => {
    const [isOpen, setIsOpen] = useState(false);

    return (
      <div className="space-y-4">
        <Button onClick={() => setIsOpen(true)}>Open modal</Button>
        <Modal {...args} isOpen={isOpen} onClose={() => setIsOpen(false)}>
          <Modal.Header>
            <div>
              <Modal.Title>Review memory capture</Modal.Title>
              <Modal.Description>Ensure the summary and tags look correct before finalizing.</Modal.Description>
            </div>
            <Modal.CloseButton />
          </Modal.Header>
          <Modal.Body>
            <p>
              Our AI generated a structured summary of today&apos;s team sync. Confirm the highlights and select which action
              items should sync to the project space.
            </p>
          </Modal.Body>
          <Modal.Footer>
            <Button onClick={() => setIsOpen(false)} variant="primary">
              Approve summary
            </Button>
            <Button onClick={() => setIsOpen(false)} variant="secondary">
              Make edits
            </Button>
          </Modal.Footer>
        </Modal>
      </div>
    );
  }
};

export const Sizes: Story = {
  render: () => {
    const [openSize, setOpenSize] = useState<"sm" | "md" | "lg" | "xl" | "full" | null>("md");

    return (
      <div className="flex flex-wrap gap-3">
        {(["sm", "md", "lg", "xl", "full"] as const).map((size) => (
          <Button key={size} onClick={() => setOpenSize(size)}>
            Open {size} modal
          </Button>
        ))}

        {openSize && (
          <Modal isOpen onClose={() => setOpenSize(null)} size={openSize} align={openSize === "full" ? "top" : "center"}>
            <Modal.Header>
              <div>
                <Modal.Title>{openSize.toUpperCase()} modal preview</Modal.Title>
                <Modal.Description>
                  Adjust sizing to match the density of the content you plan to show.
                </Modal.Description>
              </div>
              <Modal.CloseButton />
            </Modal.Header>
            <Modal.Body>
              <p>
                This layout demonstrates how modals adapt to different viewport needs. Wider layouts are ideal for complex
                monitoring dashboards or AI generated summaries, while smaller sizes keep simple confirmations approachable.
              </p>
            </Modal.Body>
            <Modal.Footer>
              <Button variant="primary" onClick={() => setOpenSize(null)}>
                Looks good
              </Button>
              <Button variant="secondary" onClick={() => setOpenSize(null)}>
                Close
              </Button>
            </Modal.Footer>
          </Modal>
        )}
      </div>
    );
  }
};

export const FocusManagement: Story = {
  render: () => {
    const [isOpen, setIsOpen] = useState(false);
    const destructiveRef = useRef<HTMLButtonElement | null>(null);

    return (
      <div className="space-y-4">
        <Button onClick={() => setIsOpen(true)} variant="danger">
          Delete memory
        </Button>
        <Modal isOpen={isOpen} onClose={() => setIsOpen(false)} initialFocusRef={destructiveRef}>
          <Modal.Header>
            <div>
              <Modal.Title>Delete this memory?</Modal.Title>
              <Modal.Description>
                This action cannot be undone and will remove all annotations tied to the memory entry.
              </Modal.Description>
            </div>
            <Modal.CloseButton />
          </Modal.Header>
          <Modal.Body>
            <p>
              The memory will no longer appear on your timeline or in generative prompts. Consider archiving if you might
              need it later.
            </p>
          </Modal.Body>
          <Modal.Footer>
            <Button ref={destructiveRef} variant="danger" onClick={() => setIsOpen(false)}>
              Permanently delete
            </Button>
            <Button variant="secondary" onClick={() => setIsOpen(false)}>
              Cancel
            </Button>
          </Modal.Footer>
        </Modal>
      </div>
    );
  }
};
