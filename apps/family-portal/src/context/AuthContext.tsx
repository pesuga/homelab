import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { User } from 'oidc-client-ts';
import { userManager, login as authLogin, logout as authLogout, getUser } from '../lib/auth';

interface AuthContextType {
    user: User | null;
    isAuthenticated: boolean;
    login: () => void;
    logout: () => void;
    loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Check for existing session
        getUser().then((user) => {
            setUser(user);
            setLoading(false);
        });

        // Listen for token renewal
        userManager.events.addUserLoaded((user) => {
            setUser(user);
        });

        userManager.events.addUserUnloaded(() => {
            setUser(null);
        });
    }, []);

    return (
        <AuthContext.Provider
            value={{
                user,
                isAuthenticated: !!user && !user.expired,
                login: authLogin,
                logout: authLogout,
                loading,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }
    return context;
}
