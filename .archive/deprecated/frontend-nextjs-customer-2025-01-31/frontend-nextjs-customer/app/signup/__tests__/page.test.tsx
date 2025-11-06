// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import '@testing-library/jest-dom/vitest';
/// <reference types="@testing-library/jest-dom" />

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { describe, expect, it, beforeEach, afterEach, vi } from 'vitest';

import SignupPage from '../page';

const signupMock = vi.fn();
const pushMock = vi.fn();

vi.mock('next/navigation', () => ({
	useRouter: () => ({
		push: pushMock,
	}),
}));

vi.mock('../../../contexts/AuthContext', () => ({
	useAuth: () => ({
		signup: signupMock,
		isLoading: false,
	}),
}));

const fillForm = () => {
	fireEvent.change(screen.getByLabelText(/Email address/i), {
		target: { value: 'Person@Example.com ' },
	});

	fireEvent.change(screen.getByLabelText(/Display name/i), {
		target: { value: '  Priya  ' },
	});

	fireEvent.change(screen.getByLabelText(/^Password$/i), {
		target: { value: 'Password1' },
	});

	fireEvent.change(screen.getByLabelText(/Confirm password/i), {
		target: { value: 'Password1' },
	});
};

describe('SignupPage', () => {
	beforeEach(() => {
		signupMock.mockReset();
		pushMock.mockReset();
	});

	afterEach(() => {
		vi.clearAllMocks();
	});

	it('renders the signup form fields', () => {
		render(<SignupPage />);

		expect(screen.getByRole('heading', { name: /Create your Ninaivalaigal account/i })).toBeInTheDocument();
		expect(screen.getByLabelText(/Email address/i)).toBeInTheDocument();
		expect(screen.getByLabelText(/Display name/i)).toBeInTheDocument();
		expect(screen.getByLabelText(/^Password$/i)).toBeInTheDocument();
		expect(screen.getByLabelText(/Confirm password/i)).toBeInTheDocument();
		expect(screen.getByRole('button', { name: /Register/i })).toBeInTheDocument();
	});

	it('shows validation errors for empty submission', async () => {
		render(<SignupPage />);

		fireEvent.click(screen.getByRole('button', { name: /Register/i }));

		expect(await screen.findByText(/Email is required/i)).toBeInTheDocument();
		expect(screen.getByText(/Password is required/i)).toBeInTheDocument();
		expect(screen.getByText(/Confirm your password/i)).toBeInTheDocument();
	});

	it('submits trimmed form data and redirects on success', async () => {
		signupMock.mockResolvedValueOnce({});
		render(<SignupPage />);

		fillForm();

		const form = document.querySelector('form');
		expect(form).not.toBeNull();
		fireEvent.submit(form!);

		await waitFor(() => {
			expect(signupMock).toHaveBeenCalledTimes(1);
		});

		expect(signupMock).toHaveBeenCalledWith({
			email: 'person@example.com',
			password: 'Password1', // pragma: allowlist secret
			username: 'Priya',
		});

		expect(pushMock).toHaveBeenCalledWith('/dashboard');
	});

	it('displays an error message when signup fails', async () => {
		signupMock.mockResolvedValueOnce({ error: 'Email already in use' });
		render(<SignupPage />);

		fillForm();

		fireEvent.click(screen.getByRole('button', { name: /Register/i }));

		expect(await screen.findByText(/Email already in use/i)).toBeInTheDocument();
		expect(pushMock).not.toHaveBeenCalled();
	});
});
