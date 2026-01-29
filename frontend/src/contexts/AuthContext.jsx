import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { login as apiLogin, getMe } from '../api/auth';
import useIdleTimeout from '../hooks/useIdleTimeout';

const AuthContext = createContext(null);

// Idle timeout: 60 minutes (3,600,000 ms)
const IDLE_TIMEOUT = 60 * 60 * 1000;

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  // Check auth status on mount
  const checkAuth = useCallback(async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    try {
      const res = await getMe();
      setUser(res.data);
    } catch (err) {
      // Token invalid or expired
      localStorage.removeItem('access_token');
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = async (email, password) => {
    const res = await apiLogin(email, password);
    const token = res.data.access_token;
    localStorage.setItem('access_token', token);

    // Fetch user info after login
    const userRes = await getMe();
    setUser(userRes.data);

    return userRes.data;
  };

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    setUser(null);
    navigate('/login');
  }, [navigate]);

  // Handle idle timeout - auto logout after inactivity
  const handleIdleTimeout = useCallback(() => {
    if (user) {
      console.log('Session expired due to inactivity');
      logout();
    }
  }, [user, logout]);

  // Enable idle timeout only when user is logged in
  useIdleTimeout(handleIdleTimeout, IDLE_TIMEOUT, !!user);

  const value = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    logout,
    checkAuth,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
