"use client";

import {
  createContext, useContext, useEffect, useState, useCallback, ReactNode,
} from "react";
import { authApi } from "@/lib/api";
import { useRouter } from "next/navigation";

interface User {
  id: string;
  email: string;
  full_name: string;
  role: "customer" | "agent" | "supervisor" | "manager" | "admin";
  status: string;
  mfa_enabled: boolean;
  department?: string;
  team_id?: string;
  team_name?: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string, mfa_code?: string) => Promise<void>;
  logout: () => Promise<void>;
  isRole: (...roles: string[]) => boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const loadUser = useCallback(async () => {
    const token = localStorage.getItem("access_token");
    if (!token) { setLoading(false); return; }

    try {
      const { data } = await authApi.me();
      setUser(data);
    } catch {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadUser(); }, [loadUser]);

  const login = async (email: string, password: string, mfa_code?: string) => {
    try {
      const { data } = await authApi.login(email, password, mfa_code);
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      const meResponse = await authApi.me();
      setUser(meResponse.data);
    } catch (err: any) {
      throw err;
    }
  };

  const logout = async () => {
    const refreshToken = localStorage.getItem("refresh_token") || "";
    try { await authApi.logout(refreshToken); } catch {}
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
    router.push("/login");
  };

  const isRole = (...roles: string[]) =>
    user ? roles.includes(user.role) : false;

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, isRole }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}



