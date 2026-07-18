"use client";

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
} from "react";
import { authApi, setToken, clearToken, ApiError } from "./api";
import type { User } from "./types";

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
  clearError: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: null,
    isLoading: true,
    error: null,
  });

  // Load existing session on mount
  useEffect(() => {
    const storedToken =
      typeof window !== "undefined"
        ? localStorage.getItem("rr_token")
        : null;

    if (!storedToken) {
      setState((s) => ({ ...s, isLoading: false }));
      return;
    }

    // Validate the stored token by fetching the user profile
    authApi
      .me()
      .then((user) => {
        setState({
          user,
          token: storedToken,
          isLoading: false,
          error: null,
        });
      })
      .catch(() => {
        // Token expired or invalid — clear and start fresh
        clearToken();
        setState({ user: null, token: null, isLoading: false, error: null });
      });
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setState((s) => ({ ...s, isLoading: true, error: null }));
    try {
      const { access_token } = await authApi.login(email, password);
      setToken(access_token);
      const user = await authApi.me();
      setState({ user, token: access_token, isLoading: false, error: null });
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail : "Login failed.";
      clearToken();
      setState((s) => ({ ...s, isLoading: false, error: msg }));
      throw err;
    }
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    setState((s) => ({ ...s, isLoading: true, error: null }));
    try {
      const { access_token } = await authApi.register(email, password);
      setToken(access_token);
      const user = await authApi.me();
      setState({ user, token: access_token, isLoading: false, error: null });
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail : "Registration failed.";
      clearToken();
      setState((s) => ({ ...s, isLoading: false, error: msg }));
      throw err;
    }
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setState({ user: null, token: null, isLoading: false, error: null });
  }, []);

  const clearError = useCallback(() => {
    setState((s) => ({ ...s, error: null }));
  }, []);

  const refreshUser = useCallback(async () => {
    try {
      const user = await authApi.me();
      setState((s) => ({ ...s, user }));
    } catch {
      // Silently fail — user profile refresh is best-effort
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{ ...state, login, register, logout, clearError, refreshUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used inside <AuthProvider>");
  }
  return ctx;
}
