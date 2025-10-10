'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error('Application error:', error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-secondary-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="w-16 h-16 bg-error-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-4xl">⚠️</span>
          </div>
          <CardTitle className="text-xl font-bold text-error-900">
            Something went wrong!
          </CardTitle>
          <CardDescription className="text-error-700">
            We encountered an unexpected error. Please try again.
          </CardDescription>
        </CardHeader>

        <CardContent>
          {error.message && (
            <div className="bg-error-50 border border-error-200 rounded-md p-3 mb-4">
              <p className="text-sm text-error-800 font-mono">{error.message}</p>
            </div>
          )}
          {error.digest && (
            <p className="text-xs text-secondary-600 text-center">
              Error ID: {error.digest}
            </p>
          )}
        </CardContent>

        <CardFooter className="flex gap-3">
          <Button
            variant="secondary"
            fullWidth
            onClick={() => window.location.href = '/'}
          >
            Go Home
          </Button>
          <Button
            fullWidth
            onClick={() => reset()}
          >
            Try Again
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
