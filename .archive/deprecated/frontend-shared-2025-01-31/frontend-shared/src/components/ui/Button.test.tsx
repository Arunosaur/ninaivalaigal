// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Button } from "./Button";

describe("Button", () => {
  it("renders children", () => {
    render(<Button>Action</Button>);
    expect(screen.getByText("Action")).toBeInTheDocument();
  });

  it("disables when loading", () => {
    render(
      <Button isLoading>
        Action
      </Button>
    );

    expect(screen.getByRole("button")).toBeDisabled();
  });
});
