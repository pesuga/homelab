/**
 * Authentication API Client
 *
 * Handles JWT token management and authenticated API requests
 */

interface LoginRequest {
  email: string;
  password: string;
}

interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

interface User {
  id: string;
  telegram_id?: number;
  first_name: string;
  last_name?: string;
  username?: string;
  role: string;
  age_group?: string;
  language_preference: string;
  is_active: boolean;
}

class AuthClient {
  private baseURL: string;
  private token: string | null = null;

  constructor(baseURL: string = '/api/v1') {
    this.baseURL = baseURL;
    // Load token from localStorage on initialization
    this.token = localStorage.getItem('auth_token');
  }

  /**
   * Authenticate user with username/password
   */
  async login(credentials: LoginRequest): Promise<TokenResponse> {
    const formData = new FormData();
    formData.append('username', credentials.email);
    formData.append('password', credentials.password);

    const response = await fetch(`${this.baseURL}/auth/login`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const tokenData: TokenResponse = await response.json();
    this.token = tokenData.access_token;
    localStorage.setItem('auth_token', this.token);

    return tokenData;
  }

  /**
   * Login with JSON request body (alternative to form data)
   */
  async loginJSON(credentials: LoginRequest): Promise<TokenResponse> {
    const response = await fetch(`${this.baseURL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const tokenData: TokenResponse = await response.json();
    this.token = tokenData.access_token;
    localStorage.setItem('auth_token', this.token);

    return tokenData;
  }

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<User> {
    const response = await this.authenticatedFetch('/auth/me');

    if (!response.ok) {
      throw new Error('Failed to get user profile');
    }

    return await response.json();
  }

  /**
   * Verify token validity
   */
  async verifyToken(): Promise<{ valid: boolean; user_id: string; role: string; username: string }> {
    const response = await this.authenticatedFetch('/auth/verify-token');

    if (!response.ok) {
      throw new Error('Token verification failed');
    }

    return await response.json();
  }

  /**
   * Logout user and clear token
   */
  logout(): void {
    this.token = null;
    localStorage.removeItem('auth_token');
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!this.token;
  }

  /**
   * Make authenticated API request
   */
  async authenticatedFetch(endpoint: string, options: RequestInit = {}): Promise<Response> {
    const url = endpoint.startsWith('http') ? endpoint : `${this.baseURL}${endpoint}`;

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    return fetch(url, {
      ...options,
      headers,
    });
  }

  /**
   * Get current token
   */
  getToken(): string | null {
    return this.token;
  }

  /**
   * Check if user has admin role
   */
  async isAdmin(): Promise<boolean> {
    try {
      const user = await this.getCurrentUser();
      return user.role === 'parent' || user.role === 'grandparent';
    } catch {
      return false;
    }
  }
}

// Export singleton instance
export const authClient = new AuthClient();
export default AuthClient;