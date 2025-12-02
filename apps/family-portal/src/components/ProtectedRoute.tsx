// import { Navigate } from 'react-router-dom';
// import { useAuth } from '../context/AuthContext';

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
    // TEMPORARY BYPASS: Always return children (disable authentication)
    // TODO: Re-enable authentication when Let's Encrypt rate limit is resolved
    return <>{children}</>;

    // Original auth logic (commented out for bypass)
    /*
    const { isAuthenticated, loading } = useAuth();

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }

    return <>{children}</>;
    */
}
