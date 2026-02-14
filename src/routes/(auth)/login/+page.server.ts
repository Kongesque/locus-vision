import { fail, redirect } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';

const API_BASE = 'http://127.0.0.1:8000';

export const load: PageServerLoad = async ({ locals }) => {
    // Redirect if already logged in
    if (locals.user) {
        throw redirect(303, '/');
    }
};

export const actions: Actions = {
    default: async ({ request, cookies }) => {
        const data = await request.formData();
        const email = data.get('email')?.toString() ?? '';
        const password = data.get('password')?.toString() ?? '';

        if (!email || !password) {
            return fail(400, { error: 'Email and password are required', email });
        }

        try {
            const res = await fetch(`${API_BASE}/api/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            if (!res.ok) {
                const body = await res.json().catch(() => ({}));
                return fail(res.status, {
                    error: body.detail || 'Invalid email or password',
                    email
                });
            }

            const tokens = await res.json();

            // Set HttpOnly cookies
            cookies.set('access_token', tokens.access_token, {
                path: '/',
                httpOnly: true,
                sameSite: 'lax',
                secure: false, // Set to true in production with HTTPS
                maxAge: 60 * 15 // 15 minutes
            });

            if (tokens.refresh_token) {
                cookies.set('refresh_token', tokens.refresh_token, {
                    path: '/',
                    httpOnly: true,
                    sameSite: 'lax',
                    secure: false,
                    maxAge: 60 * 60 * 24 * 7 // 7 days
                });
            }
        } catch {
            return fail(500, { error: 'Unable to connect to server', email });
        }

        throw redirect(303, '/');
    }
};
