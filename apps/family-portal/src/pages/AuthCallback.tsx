import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { handleCallback } from '../lib/auth';

export default function AuthCallback() {
    const navigate = useNavigate();

    useEffect(() => {
        handleCallback()
            .then(() => {
                navigate('/');
            })
            .catch((error) => {
                console.error('Auth callback error:', error);
                navigate('/login?error=callback_failed');
            });
    }, [navigate]);

    return (
        <div className="flex items-center justify-center min-h-screen">
            <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <h2 className="text-xl font-semibold mb-2">Processing login...</h2>
                <p className="text-gray-600">Please wait while we complete your authentication.</p>
            </div>
        </div>
    );
}
