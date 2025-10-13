// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-secondary-50">
      {/* Hero Section */}
      <main className="container mx-auto px-4 py-16 sm:py-24">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h1 className="text-4xl sm:text-6xl font-bold text-secondary-900 mb-6">
            Welcome to{' '}
            <span className="text-primary-600">Ninaivalaigal</span>
          </h1>
          <p className="text-lg sm:text-xl text-secondary-600 mb-8">
            Your personal memory garden. Capture, connect, and cultivate your memories with AI-powered insights.
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <Link href="/signup">
              <Button size="lg">
                Get Started →
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button size="lg" variant="secondary">
                View Dashboard
              </Button>
            </Link>
          </div>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          <Card>
            <CardHeader>
              <div className="text-4xl mb-2">🧠</div>
              <CardTitle>Smart Memory Capture</CardTitle>
              <CardDescription>
                Capture your thoughts with AI-assisted tagging and context detection
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="text-sm text-secondary-600 space-y-2">
                <li>• Auto-tagging with ML</li>
                <li>• Sentiment analysis</li>
                <li>• Smart linking</li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="text-4xl mb-2">📊</div>
              <CardTitle>Visual Analytics</CardTitle>
              <CardDescription>
                Track your memory patterns and insights over time
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="text-sm text-secondary-600 space-y-2">
                <li>• Sentiment trends</li>
                <li>• Topic analysis</li>
                <li>• Engagement metrics</li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="text-4xl mb-2">🏆</div>
              <CardTitle>Gamification</CardTitle>
              <CardDescription>
                Earn badges and track your progress as you build your memory collection
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="text-sm text-secondary-600 space-y-2">
                <li>• Achievement badges</li>
                <li>• Team rankings</li>
                <li>• Progress tracking</li>
              </ul>
            </CardContent>
          </Card>
        </div>

        {/* CTA Section */}
        <div className="mt-16 text-center">
          <Card className="max-w-2xl mx-auto bg-primary-50 border-primary-200">
            <CardHeader>
              <CardTitle className="text-2xl">Ready to Start?</CardTitle>
              <CardDescription className="text-base">
                Join thousands of users building their memory gardens
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link href="/signup">
                <Button size="lg" fullWidth>
                  Create Your Account
                </Button>
              </Link>
              <p className="text-sm text-secondary-600 mt-4">
                Already have an account?{' '}
                <Link href="/login" className="text-primary-600 hover:text-primary-700 font-medium">
                  Log in
                </Link>
              </p>
            </CardContent>
          </Card>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-secondary-200 bg-white">
        <div className="container mx-auto px-4 py-8">
          <div className="flex flex-wrap justify-between items-center gap-4">
            <p className="text-sm text-secondary-600">
              © 2025 Ninaivalaigal. Built with Next.js 15.
            </p>
            <div className="flex gap-6 text-sm">
              <a href="/about" className="text-secondary-600 hover:text-primary-600">
                About
              </a>
              <a href="/docs" className="text-secondary-600 hover:text-primary-600">
                Docs
              </a>
              <a href="/privacy" className="text-secondary-600 hover:text-primary-600">
                Privacy
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
