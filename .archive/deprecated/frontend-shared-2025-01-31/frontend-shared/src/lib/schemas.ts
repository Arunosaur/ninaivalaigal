// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { z } from "zod";

export const sessionSchema = z.object({
  userId: z.string(),
  email: z.string().email(),
  displayName: z.string(),
  roles: z.array(z.string()),
  token: z.string(),
  expiresAt: z.string().datetime()
});

export type Session = z.infer<typeof sessionSchema>;

export const notificationSchema = z.object({
  id: z.string(),
  title: z.string(),
  message: z.string(),
  createdAt: z.string().datetime(),
  variant: z.enum(["info", "success", "warning", "error"])
});

export type Notification = z.infer<typeof notificationSchema>;
