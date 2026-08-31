import { renderHook, act } from "@testing-library/react";
import { AuthProvider, useAuth } from "@/lib/auth-context";
import { jest } from "@jest/globals";
import React from "react";

// Mock Next.js navigation
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
}));



import { authApi } from "@/lib/api";

describe("AuthContext", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("provides null user initially when no token", () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => <AuthProvider>{children}</AuthProvider>;
    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.user).toBeNull();
  });

  it("logs in successfully", async () => {
    const mockUser = { id: "user-1", email: "test@example.com", role: "agent" };
    jest.spyOn(authApi, 'login').mockResolvedValueOnce({
      data: {
        access_token: "test-token",
        user: mockUser,
      }
    } as any);
    jest.spyOn(authApi, 'me').mockResolvedValueOnce({
      data: mockUser
    } as any);

    const wrapper = ({ children }: { children: React.ReactNode }) => <AuthProvider>{children}</AuthProvider>;
    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.login("test@example.com", "password");
    });

    expect(result.current.user).toEqual(mockUser);
  });

  it("logs out successfully", async () => {
    jest.spyOn(authApi, 'logout').mockResolvedValueOnce({ data: {} } as any);

    const wrapper = ({ children }: { children: React.ReactNode }) => <AuthProvider>{children}</AuthProvider>;
    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.logout();
    });

    expect(result.current.user).toBeNull();
  });
});
