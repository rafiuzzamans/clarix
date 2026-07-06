import { renderHook, act } from "@testing-library/react";
import { AuthProvider, useAuth } from "@/lib/auth-context";
import { jest } from "@jest/globals";
import React from "react";

// Mock the API interactions for login/logout
jest.mock("@/lib/api", () => ({
  login: jest.fn(),
  logout: jest.fn(),
  getCurrentUser: jest.fn(),
}));

import { login, logout, getCurrentUser } from "@/lib/api";

describe("AuthContext", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("provides null user initially when no token", () => {
    (getCurrentUser as jest.Mock).mockRejectedValueOnce(new Error("No token"));
    const wrapper = ({ children }: { children: React.ReactNode }) => <AuthProvider>{children}</AuthProvider>;
    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  it("logs in successfully", async () => {
    const mockUser = { id: "user-1", email: "test@example.com", role: "agent" };
    (login as jest.Mock).mockResolvedValueOnce({
      access_token: "test-token",
      user: mockUser,
    });

    const wrapper = ({ children }: { children: React.ReactNode }) => <AuthProvider>{children}</AuthProvider>;
    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.login("test@example.com", "password");
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isAuthenticated).toBe(true);
  });

  it("logs out successfully", async () => {
    (logout as jest.Mock).mockResolvedValueOnce(undefined);
    
    const wrapper = ({ children }: { children: React.ReactNode }) => <AuthProvider>{children}</AuthProvider>;
    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.logout();
    });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });
});
