import { screen, fireEvent, waitFor } from "@testing-library/react";
import { render } from "../jest-utils";
import "@testing-library/jest-dom";
import { jest } from "@jest/globals";
import { AuthContext } from "@/lib/auth-context";

// Mock Next.js navigation
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
}));

// Mock react-hot-toast
jest.mock("react-hot-toast", () => ({
  __esModule: true,
  default: { success: jest.fn(), error: jest.fn() },
}));

const mockLogin = jest.fn<any>();

const renderWithAuth = (ui: React.ReactElement) => {
  return render(
    <AuthContext.Provider value={{
      user: null,
      loading: false,
      login: mockLogin as any,
      logout: jest.fn() as any,
      isRole: jest.fn() as any
    }}>
      {ui}
    </AuthContext.Provider>
  );
};

import LoginPage from "@/app/login/page";

describe("LoginPage", () => {
  beforeEach(() => {
    mockLogin.mockClear();
  });

  it("renders email and password fields", () => {
    renderWithAuth(<LoginPage />);
    expect(screen.getByPlaceholderText("you@company.com")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("••••••••")).toBeInTheDocument();
  });

  it("renders demo account buttons", () => {
    renderWithAuth(<LoginPage />);
    expect(screen.queryByText("Admin")).toBeTruthy();
  });

  it("shows sign in button", () => {
    renderWithAuth(<LoginPage />);
    const btn = screen.getByText("Sign in");
    expect(btn).toBeInTheDocument();
  });

  it("calls login on form submit", async () => {
    mockLogin.mockResolvedValue(undefined);
    renderWithAuth(<LoginPage />);

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
    renderWithAuth(<LoginPage />);

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
