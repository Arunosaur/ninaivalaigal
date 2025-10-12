'use client';

import { useRouter } from 'next/navigation';
import { LoginForm } from '@ninaivalaigal/ui-components';

export default function LoginPage() {
  const router = useRouter();

  const handleSuccess = () => {
    router.push('/dashboard');
  };

  const handleError = (error: Error) => {
    console.error('Login failed:', error);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-md space-y-8 rounded-lg bg-white p-8 shadow">
        <div className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-gray-900">
            Welcome Back
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Sign in to your Ninaivalaigal account
          </p>
        </div>

        <div className="mt-8">
          <LoginForm onSuccess={handleSuccess} onError={handleError} />
        </div>

        <div className="text-center text-sm text-gray-600">
          Don't have an account?{' '}
          <a href="#" className="font-medium text-blue-600 hover:text-blue-500">
            Sign up
          </a>
        </div>
      </div>
    </div>
  );
}
