// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-secondary-50 p-4">
      <Card className="w-full max-w-md text-center">
        <CardHeader>
          <div className="text-6xl font-bold text-primary-600 mb-2">404</div>
          <CardTitle className="text-2xl">Page Not Found</CardTitle>
          <CardDescription>
            The page you're looking for doesn't exist or has been moved.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <div className="text-secondary-600 text-sm space-y-2">
            <p>Here are some helpful links:</p>
            <div className="flex flex-col gap-2 mt-4">
              <a href="/" className="text-primary-600 hover:text-primary-700 hover:underline">
                → Home
              </a>
              <a href="/dashboard" className="text-primary-600 hover:text-primary-700 hover:underline">
                → Dashboard
              </a>
              <a href="/signup" className="text-primary-600 hover:text-primary-700 hover:underline">
                → Sign Up
              </a>
            </div>
          </div>
        </CardContent>

        <CardFooter>
          <Button
            fullWidth
            onClick={() => window.history.back()}
          >
            ← Go Back
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
