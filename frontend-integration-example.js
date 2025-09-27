// Frontend integration example for GET-based auth
// Use this pattern in your UI components

class AuthService {
    constructor(baseUrl = 'http://localhost:13370') {
        this.baseUrl = baseUrl;
        this.token = localStorage.getItem('jwt_token');
    }

    async login(email, password) {
        try {
            const response = await fetch(
                `${this.baseUrl}/auth-working/login?email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`
            );

            const data = await response.json();

            if (data.success) {
                this.token = data.jwt_token;
                localStorage.setItem('jwt_token', this.token);
                localStorage.setItem('user_info', JSON.stringify({
                    user_id: data.user_id,
                    email: data.email,
                    account_type: data.account_type,
                    role: data.role
                }));
                return { success: true, user: data };
            } else {
                return { success: false, error: data.error };
            }
        } catch (error) {
            return { success: false, error: `Login failed: ${error.message}` };
        }
    }

    async validateToken() {
        if (!this.token) return { valid: false, error: 'No token' };

        try {
            const response = await fetch(
                `${this.baseUrl}/auth-working/validate-token?token=${encodeURIComponent(this.token)}`
            );
            return await response.json();
        } catch (error) {
            return { valid: false, error: error.message };
        }
    }

    logout() {
        this.token = null;
        localStorage.removeItem('jwt_token');
        localStorage.removeItem('user_info');
    }

    isLoggedIn() {
        return !!this.token;
    }

    getAuthHeaders() {
        return this.token ? { 'Authorization': `Bearer ${this.token}` } : {};
    }
}

// Usage example:
const auth = new AuthService();

// Login
const loginResult = await auth.login('user@example.com', 'password');
if (loginResult.success) {
    console.log('Login successful:', loginResult.user);
} else {
    console.error('Login failed:', loginResult.error);
}

// Validate token
const validation = await auth.validateToken();
if (validation.valid) {
    console.log('Token valid, user:', validation);
} else {
    console.log('Token invalid, redirecting to login');
}
