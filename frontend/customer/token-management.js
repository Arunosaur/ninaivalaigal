// Token Management JavaScript
// Handles JWT token display, regeneration, API key management, and usage analytics

class TokenManager {
    constructor() {
        this.apiBase = 'http://localhost:8000'; // TODO: Make configurable
        this.currentToken = localStorage.getItem('authToken');
        this.init();
    }

    async init() {
        if (!this.currentToken) {
            window.location.href = 'login.html';
            return;
        }

        await this.loadUserInfo();
        await this.loadCurrentToken();
        await this.loadApiKeys();
        await this.loadUsageAnalytics();
        this.setupEventListeners();
    }

    async loadUserInfo() {
        try {
            const response = await fetch(`${this.apiBase}/auth/me`, {
                headers: {
                    'Authorization': `Bearer ${this.currentToken}`
                }
            });

            if (response.ok) {
                const user = await response.json();
                document.getElementById('user-name').textContent = user.email || user.username;
            }
        } catch (error) {
            console.error('Failed to load user info:', error);
        }
    }

    async loadCurrentToken() {
        try {
            // Decode JWT to get token info (basic client-side parsing)
            const tokenInfo = this.parseJWT(this.currentToken);

            document.getElementById('current-token').textContent = this.currentToken;

            if (tokenInfo) {
                const issuedDate = new Date(tokenInfo.iat * 1000);
                const expiresDate = new Date(tokenInfo.exp * 1000);
                const now = new Date();

                document.getElementById('token-issued').textContent = issuedDate.toLocaleDateString();
                document.getElementById('token-expires').textContent = expiresDate.toLocaleDateString();

                // Update status based on expiration
                const statusElement = document.getElementById('token-status');
                if (expiresDate < now) {
                    statusElement.textContent = 'Expired';
                    statusElement.className = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800';
                } else if (expiresDate - now < 7 * 24 * 60 * 60 * 1000) { // 7 days
                    statusElement.textContent = 'Expiring Soon';
                    statusElement.className = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800';
                } else {
                    statusElement.textContent = 'Active';
                    statusElement.className = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800';
                }
            }
        } catch (error) {
            console.error('Failed to parse token:', error);
            document.getElementById('current-token').textContent = 'Error loading token';
        }
    }

    async loadApiKeys() {
        try {
            const response = await fetch(`${this.apiBase}/auth/api-keys`, {
                headers: {
                    'Authorization': `Bearer ${this.currentToken}`
                }
            });

            if (response.ok) {
                const apiKeys = await response.json();
                this.renderApiKeys(apiKeys);
            } else {
                // If endpoint doesn't exist yet, show placeholder
                this.renderApiKeysPlaceholder();
            }
        } catch (error) {
            console.error('Failed to load API keys:', error);
            this.renderApiKeysPlaceholder();
        }
    }

    renderApiKeys(apiKeys) {
        const container = document.getElementById('api-keys-list');
        const noKeysMessage = document.getElementById('no-api-keys');

        if (apiKeys.length === 0) {
            container.innerHTML = '';
            noKeysMessage.classList.remove('hidden');
            return;
        }

        noKeysMessage.classList.add('hidden');
        container.innerHTML = apiKeys.map(key => `
            <div class="border border-gray-200 rounded-lg p-4">
                <div class="flex items-center justify-between">
                    <div class="flex-1">
                        <h4 class="font-medium text-gray-900">${key.name}</h4>
                        <div class="text-sm text-gray-600 mt-1">
                            <span>Created: ${new Date(key.created_at).toLocaleDateString()}</span>
                            <span class="mx-2">•</span>
                            <span>Expires: ${key.expires_at ? new Date(key.expires_at).toLocaleDateString() : 'Never'}</span>
                            <span class="mx-2">•</span>
                            <span>Last used: ${key.last_used_at ? new Date(key.last_used_at).toLocaleDateString() : 'Never'}</span>
                        </div>
                        <div class="mt-2">
                            <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${key.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                                ${key.is_active ? 'Active' : 'Inactive'}
                            </span>
                            ${key.permissions ? key.permissions.map(perm => `
                                <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 ml-1">
                                    ${perm}
                                </span>
                            `).join('') : ''}
                        </div>
                    </div>
                    <div class="flex space-x-2 ml-4">
                        <button onclick="copyApiKey('${key.id}')" class="text-blue-600 hover:text-blue-800 text-sm">
                            📋 Copy
                        </button>
                        <button onclick="revokeApiKey('${key.id}')" class="text-red-600 hover:text-red-800 text-sm">
                            🗑️ Revoke
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    renderApiKeysPlaceholder() {
        const container = document.getElementById('api-keys-list');
        const noKeysMessage = document.getElementById('no-api-keys');

        container.innerHTML = `
            <div class="border border-gray-200 rounded-lg p-4 bg-gray-50">
                <div class="text-center text-gray-500">
                    <p class="text-sm">API key management will be available once backend endpoints are implemented.</p>
                    <p class="text-xs mt-1">Coming soon in Phase 1 implementation!</p>
                </div>
            </div>
        `;
        noKeysMessage.classList.add('hidden');
    }

    async loadUsageAnalytics() {
        try {
            const response = await fetch(`${this.apiBase}/auth/token-usage`, {
                headers: {
                    'Authorization': `Bearer ${this.currentToken}`
                }
            });

            if (response.ok) {
                const usage = await response.json();
                this.renderUsageAnalytics(usage);
            } else {
                this.renderUsageAnalyticsPlaceholder();
            }
        } catch (error) {
            console.error('Failed to load usage analytics:', error);
            this.renderUsageAnalyticsPlaceholder();
        }
    }

    renderUsageAnalytics(usage) {
        document.getElementById('requests-today').textContent = usage.requests_today || '0';
        document.getElementById('requests-week').textContent = usage.requests_week || '0';
        document.getElementById('last-used').textContent = usage.last_used ? new Date(usage.last_used).toLocaleDateString() : 'Never';
        document.getElementById('rate-limit').textContent = `${usage.rate_limit_remaining || 0}/${usage.rate_limit_total || 1000}`;

        const activityContainer = document.getElementById('recent-activity');
        if (usage.recent_activity && usage.recent_activity.length > 0) {
            activityContainer.innerHTML = usage.recent_activity.map(activity => `
                <div class="flex justify-between text-sm">
                    <span class="text-gray-600">${activity.endpoint}</span>
                    <span class="text-gray-500">${new Date(activity.timestamp).toLocaleString()}</span>
                </div>
            `).join('');
        } else {
            activityContainer.innerHTML = '<div class="text-sm text-gray-500">No recent activity</div>';
        }
    }

    renderUsageAnalyticsPlaceholder() {
        document.getElementById('requests-today').textContent = '-';
        document.getElementById('requests-week').textContent = '-';
        document.getElementById('last-used').textContent = '-';
        document.getElementById('rate-limit').textContent = '-';

        document.getElementById('recent-activity').innerHTML = `
            <div class="text-sm text-gray-500">Usage analytics will be available once backend endpoints are implemented.</div>
        `;
    }

    setupEventListeners() {
        // Create API Key form
        document.getElementById('create-api-key-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleCreateApiKey();
        });

        // Auto rotation toggle
        document.getElementById('auto-rotation').addEventListener('change', (e) => {
            this.handleAutoRotationToggle(e.target.checked);
        });
    }

    parseJWT(token) {
        try {
            const base64Url = token.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
                return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
            }).join(''));
            return JSON.parse(jsonPayload);
        } catch (error) {
            console.error('Failed to parse JWT:', error);
            return null;
        }
    }

    async handleCreateApiKey() {
        const name = document.getElementById('api-key-name').value;
        const expiration = document.getElementById('api-key-expiration').value;
        const permissions = Array.from(document.querySelectorAll('#create-api-key-form input[type="checkbox"]:checked'))
            .map(cb => cb.value);

        try {
            const response = await fetch(`${this.apiBase}/auth/api-keys`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.currentToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name,
                    expiration: expiration === 'never' ? null : parseInt(expiration),
                    permissions
                })
            });

            if (response.ok) {
                const newKey = await response.json();
                this.showApiKeyCreated(newKey);
                this.closeCreateApiKeyModal();
                await this.loadApiKeys();
            } else {
                alert('Failed to create API key. Please try again.');
            }
        } catch (error) {
            console.error('Failed to create API key:', error);
            alert('Failed to create API key. Backend endpoint not yet implemented.');
        }
    }

    showApiKeyCreated(apiKey) {
        // Show the new API key in a modal (only shown once for security)
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                <h3 class="text-lg font-semibold text-gray-900 mb-4">API Key Created</h3>
                <p class="text-sm text-gray-600 mb-4">
                    Your API key has been created. Copy it now - you won't be able to see it again!
                </p>
                <div class="token-display mb-4">${apiKey.key}</div>
                <div class="flex space-x-3">
                    <button onclick="navigator.clipboard.writeText('${apiKey.key}'); this.textContent='Copied!'"
                            class="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors">
                        Copy Key
                    </button>
                    <button onclick="this.closest('.fixed').remove()"
                            class="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-700 px-4 py-2 rounded-lg transition-colors">
                        Close
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    async handleAutoRotationToggle(enabled) {
        try {
            const response = await fetch(`${this.apiBase}/auth/settings`, {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${this.currentToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    auto_token_rotation: enabled
                })
            });

            if (!response.ok) {
                console.log('Auto rotation setting will be saved once backend endpoint is implemented');
            }
        } catch (error) {
            console.error('Failed to update auto rotation setting:', error);
        }
    }
}

// Global functions for button clicks
async function copyToken() {
    const token = document.getElementById('current-token').textContent;
    try {
        await navigator.clipboard.writeText(token);
        showNotification('Token copied to clipboard!', 'success');
    } catch (error) {
        console.error('Failed to copy token:', error);
        showNotification('Failed to copy token', 'error');
    }
}

async function regenerateToken() {
    if (!confirm('Are you sure you want to regenerate your token? This will invalidate your current token.')) {
        return;
    }

    try {
        const tokenManager = window.tokenManager;
        const response = await fetch(`${tokenManager.apiBase}/auth/regenerate-token`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${tokenManager.currentToken}`
            }
        });

        if (response.ok) {
            const result = await response.json();
            localStorage.setItem('authToken', result.token);
            tokenManager.currentToken = result.token;
            await tokenManager.loadCurrentToken();
            showNotification('Token regenerated successfully!', 'success');
        } else {
            showNotification('Failed to regenerate token', 'error');
        }
    } catch (error) {
        console.error('Failed to regenerate token:', error);
        showNotification('Token regeneration will be available once backend endpoint is implemented', 'info');
    }
}

function createApiKey() {
    document.getElementById('create-api-key-modal').classList.remove('hidden');
    document.getElementById('create-api-key-modal').classList.add('flex');
}

function closeCreateApiKeyModal() {
    document.getElementById('create-api-key-modal').classList.add('hidden');
    document.getElementById('create-api-key-modal').classList.remove('flex');
    document.getElementById('create-api-key-form').reset();
}

async function copyApiKey(keyId) {
    showNotification('API key copying will be available once backend is implemented', 'info');
}

async function revokeApiKey(keyId) {
    if (!confirm('Are you sure you want to revoke this API key? This action cannot be undone.')) {
        return;
    }

    try {
        const tokenManager = window.tokenManager;
        const response = await fetch(`${tokenManager.apiBase}/auth/api-keys/${keyId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${tokenManager.currentToken}`
            }
        });

        if (response.ok) {
            await tokenManager.loadApiKeys();
            showNotification('API key revoked successfully!', 'success');
        } else {
            showNotification('Failed to revoke API key', 'error');
        }
    } catch (error) {
        console.error('Failed to revoke API key:', error);
        showNotification('API key revocation will be available once backend endpoint is implemented', 'info');
    }
}

function manageIpRestrictions() {
    showNotification('IP restrictions management will be available in a future update', 'info');
}

async function revokeAllTokens() {
    if (!confirm('Are you sure you want to revoke ALL tokens? This will log you out and invalidate all API keys.')) {
        return;
    }

    try {
        const tokenManager = window.tokenManager;
        const response = await fetch(`${tokenManager.apiBase}/auth/revoke-all`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${tokenManager.currentToken}`
            }
        });

        if (response.ok) {
            localStorage.removeItem('authToken');
            showNotification('All tokens revoked. Redirecting to login...', 'success');
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 2000);
        } else {
            showNotification('Failed to revoke all tokens', 'error');
        }
    } catch (error) {
        console.error('Failed to revoke all tokens:', error);
        showNotification('Token revocation will be available once backend endpoint is implemented', 'info');
    }
}

function logout() {
    localStorage.removeItem('authToken');
    window.location.href = 'login.html';
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    const bgColor = type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500';

    notification.className = `fixed top-4 right-4 ${bgColor} text-white px-6 py-3 rounded-lg shadow-lg z-50 transition-opacity duration-300`;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.tokenManager = new TokenManager();
});
