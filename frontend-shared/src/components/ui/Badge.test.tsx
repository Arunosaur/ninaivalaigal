// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Badge } from "./Badge";

describe("Badge", () => {
  it("renders children", () => {
    render(<Badge>Personal</Badge>);
    expect(screen.getByText("Personal")).toBeInTheDocument();
  });

  it("applies pill style when requested", () => {
    render(<Badge pill>Rounded</Badge>);
    const badge = screen.getByText("Rounded");
    expect(badge.className).toContain("rounded-full");
  });

  it("supports different variants", () => {
    render(<Badge variant="success">Success</Badge>);
    const badge = screen.getByText("Success");
    expect(badge.className).toContain("bg-emerald-100");
  });
});
