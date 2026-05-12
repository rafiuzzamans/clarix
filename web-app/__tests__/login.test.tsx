import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { jest } from "@jest/globals";

// Mock Next.js navigation
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
}));

// Mock react-hot-toast
jest.mock("react-hot-toast", () => ({
  __esModule: true,
  default: { success: jest.fn(), error: jest.fn() },
}));

// Mock auth context
const mockLogin = jest.fn();
jest.mock("@/lib/auth-context", () => ({
  useAuth: () => ({ login: mockLogin }),
}));

import LoginPage from "@/app/login/page";

describe("LoginPage", () => {
  beforeEach(() => {
    mockLogin.mockClear();
  });

  it("renders email and password fields", () => {
    render(<LoginPage />);
    expect(screen.getByPlaceholderText("you@company.com")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("••••••••")).toBeInTheDocument();
  });

  it("renders demo account buttons", () => {
    render(<LoginPage />);
    expect(screen.getByTestId ? screen.queryByText("Admin") : screen.queryByText("Admin")).toBeTruthy();
  });

  it("shows sign in button", () => {
    render(<LoginPage />);
    const btn = screen.getByText("Sign in");
    expect(btn).toBeInTheDocument();
  });

  it("calls login on form submit", async () => {
    mockLogin.mockResolvedValue(undefined);
    render(<LoginPage />);

    fireEvent.change(screen.getByPlaceholderText("you@company.com"), {
      target: { value: "admin@csplatform.local" },
    });
    fireEvent.change(screen.getByPlaceholderText("••••••••"), {
      target: { value: "Admin@123" },
    });
    fireEvent.click(screen.getByText("Sign in"));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith(
        "admin@csplatform.local",
        "Admin@123",
        undefined
      );
    });
  });

  it("shows MFA field on MFA required error", async () => {
    mockLogin.mockRejectedValue({
      response: { data: { detail: "MFA code required" } },
    });
    render(<LoginPage />);

    fireEvent.change(screen.getByPlaceholderText("you@company.com"), {
      target: { value: "admin@csplatform.local" },
    });
    fireEvent.change(screen.getByPlaceholderText("••••••••"), {
      target: { value: "Admin@123" },
    });
    fireEvent.click(screen.getByText("Sign in"));

    await waitFor(() => {
      expect(screen.queryByPlaceholderText("000000")).toBeTruthy();
    });
  });
});
