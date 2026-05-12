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
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isMockMode: boolean;
  login: (email: string, password: string, mfa_code?: string) => Promise<void>;
  logout: () => Promise<void>;
  isRole: (...roles: string[]) => boolean;
}

// ── Demo accounts for offline/mock mode ──────────────────────────────────────
const MOCK_PASSWORD = "Admin@123";
const MOCK_USERS: Record<string, User> = {
  "admin@csplatform.local": {
    id: "mock-admin-1",
    email: "admin@csplatform.local",
    full_name: "Alex Admin",
    role: "admin",
    status: "active",
    mfa_enabled: false,
    department: "Operations",
  },
  "manager@csplatform.local": {
    id: "mock-manager-1",
    email: "manager@csplatform.local",
    full_name: "Morgan Manager",
    role: "manager",
    status: "active",
    mfa_enabled: false,
    department: "Customer Success",
  },
  "agent1@csplatform.local": {
    id: "mock-agent-1",
    email: "agent1@csplatform.local",
    full_name: "Sam Agent",
    role: "agent",
    status: "active",
    mfa_enabled: false,
    department: "Support",
  },
  "customer@csplatform.local": {
    id: "mock-customer-1",
    email: "customer@csplatform.local",
    full_name: "Chris Customer",
    role: "customer",
    status: "active",
    mfa_enabled: false,
  },
};

const MOCK_TOKEN = "mock-jwt-token-offline-demo";

function isNetworkError(err: any): boolean {
  return (
    !err?.response ||
    err?.code === "ERR_NETWORK" ||
    err?.code === "ECONNABORTED" ||
    err?.message === "Network Error"
  );
}

// ─────────────────────────────────────────────────────────────────────────────

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [isMockMode, setIsMockMode] = useState(false);
  const router = useRouter();

  const loadUser = useCallback(async () => {
    const token = localStorage.getItem("access_token");
    if (!token) { setLoading(false); return; }

    // Restore mock session without hitting the network
    if (token === MOCK_TOKEN) {
      const stored = localStorage.getItem("mock_user");
      if (stored) {
        setUser(JSON.parse(stored));
        setIsMockMode(true);
      }
      setLoading(false);
      return;
    }

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
      setUser(data.user);
      setIsMockMode(false);
    } catch (err: any) {
      // If backend is unreachable, try mock login
      if (isNetworkError(err)) {
        const mockUser = MOCK_USERS[email.toLowerCase()];
        if (mockUser && password === MOCK_PASSWORD) {
          localStorage.setItem("access_token", MOCK_TOKEN);
          localStorage.setItem("mock_user", JSON.stringify(mockUser));
          setUser(mockUser);
          setIsMockMode(true);
          return;
        }
        // Network is down and credentials don't match a demo account
        throw Object.assign(new Error("Network Error"), {
          response: {
            data: { detail: "Backend offline — use a demo account with password Admin@123" },
          },
        });
      }
      // Real API error (e.g. 401 wrong password) — re-throw as-is
      throw err;
    }
  };

  const logout = async () => {
    const refreshToken = localStorage.getItem("refresh_token") || "";
    if (!isMockMode) {
      try { await authApi.logout(refreshToken); } catch {}
    }
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("mock_user");
    setUser(null);
    setIsMockMode(false);
    router.push("/login");
  };

  const isRole = (...roles: string[]) =>
    user ? roles.includes(user.role) : false;

  return (
    <AuthContext.Provider value={{ user, loading, isMockMode, login, logout, isRole }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
