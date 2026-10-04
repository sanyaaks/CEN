"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { User, LoginCredentials, DemoPersona } from "../types/auth";
import { loginOfficial, getCurrentUserProfile, logoutOfficial } from "../lib/api";

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginCredentials) => Promise<boolean>;
  logout: () => Promise<void>;
  quickLoginAs: (persona: DemoPersona) => Promise<boolean>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
  login: async () => false,
  logout: async () => {},
  quickLoginAs: async () => false,
  clearError: () => {},
});

export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Initialize and verify existing session from localStorage
  useEffect(() => {
    async function initAuth() {
      try {
        const storedToken = localStorage.getItem("mospi_auth_token");
        const storedUser = localStorage.getItem("mospi_auth_user");

        if (storedToken) {
          setToken(storedToken);
          if (storedUser) {
            try {
              setUser(JSON.parse(storedUser));
            } catch {
              // fallback
            }
          }

          // Verify token against backend
          try {
            const verifiedProfile = await getCurrentUserProfile();
            setUser(verifiedProfile);
            localStorage.setItem("mospi_auth_user", JSON.stringify(verifiedProfile));
          } catch (profileErr) {
            console.warn("Stored auth token verification failed, clearing session:", profileErr);
            localStorage.removeItem("mospi_auth_token");
            localStorage.removeItem("mospi_auth_user");
            setToken(null);
            setUser(null);
          }
        }
      } catch (err) {
        console.error("Error during auth initialization:", err);
      } finally {
        setIsLoading(false);
      }
    }

    initAuth();
  }, []);

  // Login handler
  const login = async (credentials: LoginCredentials): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    try {
      const resp = await loginOfficial(credentials);
      setToken(resp.access_token);
      setUser(resp.user);
      localStorage.setItem("mospi_auth_token", resp.access_token);
      localStorage.setItem("mospi_auth_user", JSON.stringify(resp.user));
      return true;
    } catch (err: any) {
      const msg = err.message?.replace(/^API Error \[\d+\]:\s*/, "") || "Authentication failed. Please verify credentials.";
      setError(msg);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  // 1-Click quick login as demo persona
  const quickLoginAs = async (persona: DemoPersona): Promise<boolean> => {
    return login({
      email: persona.email,
      password: persona.password,
    });
  };

  // Logout handler
  const logout = async (): Promise<void> => {
    try {
      if (token) {
        await logoutOfficial();
      }
    } catch (err) {
      console.warn("Logout notification error:", err);
    } finally {
      setToken(null);
      setUser(null);
      setError(null);
      localStorage.removeItem("mospi_auth_token");
      localStorage.removeItem("mospi_auth_user");
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user && !!token,
        isLoading,
        error,
        login,
        logout,
        quickLoginAs,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
