import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import apiService from '../services/api.ts';
import { toast } from 'react-toastify';

export type UserRole = 'citoyen' | 'admin_public' | 'admin_plateforme';

interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  is_admin: boolean;
  is_admin_plateforme: boolean;
  is_admin_public: boolean;
  is_citoyen: boolean;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (userData: RegisterData) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

interface RegisterData {
  email: string;
  first_name: string;
  last_name: string;
  password: string;
  password_confirm: string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Vérifier si l'utilisateur est connecté au chargement
    const token = localStorage.getItem('access_token');
    if (token) {
      checkAuthStatus();
    } else {
      setLoading(false);
    }
  }, []);

  const checkAuthStatus = async () => {
    try {
      const response = await apiService.getCurrentUser();
      setUser(response.data);
    } catch (error) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    try {
      const response = await apiService.login({ email, password });

      const { access, refresh, user } = response.data;
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);

      setUser(user);

      toast.success('Connexion réussie !');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur de connexion');
      throw error;
    }
  };

  const register = async (userData: RegisterData) => {
    try {
      await apiService.register(userData);
      toast.success('Inscription réussie ! Vous pouvez maintenant vous connecter.');
    } catch (error: any) {
      const errorMessage = error.response?.data?.email?.[0] ||
                          error.response?.data?.password?.[0] ||
                          'Erreur lors de l\'inscription';
      toast.error(errorMessage);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
    toast.info('Déconnexion réussie');
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    loading,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
