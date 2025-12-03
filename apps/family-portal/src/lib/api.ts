import axios from 'axios';
import { getUser } from './auth';

const API_BASE_URL = 'https://api.fa.pesulabs.net';

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add auth token to requests
apiClient.interceptors.request.use(async (config) => {
    const user = await getUser();
    if (user && user.access_token) {
        config.headers.Authorization = `Bearer ${user.access_token}`;
    }
    return config;
});

// Handle 401 errors
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Token expired, redirect to login
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

export default apiClient;

// Example usage:
export async function fetchPrompts() {
    const response = await apiClient.get('/api/phase2/prompts/core');
    return response.data;
}
