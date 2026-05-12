import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { jest } from "@jest/globals";

jest.mock("@tanstack/react-query", () => ({
  useMutation: () => ({ mutate: jest.fn(), isPending: false }),
  useQueryClient: () => ({ invalidateQueries: jest.fn() }),
}));

import CreateCaseModal from "@/components/cases/CreateCaseModal";

describe("CreateCaseModal", () => {
  const onClose   = jest.fn();
  const onCreated = jest.fn();

  beforeEach(() => {
    onClose.mockClear();
    onCreated.mockClear();
  });

  it("renders title and message fields", () => {
    render(<CreateCaseModal onClose={onClose} onCreated={onCreated} />);
    expect(screen.getByPlaceholderText(/brief summary/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/describe the issue/i)).toBeInTheDocument();
  });

  it("shows AI auto-predict label", () => {
    render(<CreateCaseModal onClose={onClose} onCreated={onCreated} />);
    expect(screen.getByText(/AI will auto-classify/i)).toBeInTheDocument();
  });

  it("calls onClose when Cancel is clicked", () => {
    render(<CreateCaseModal onClose={onClose} onCreated={onCreated} />);
    fireEvent.click(screen.getByText("Cancel"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("submit button is disabled when title/message are empty", () => {
    render(<CreateCaseModal onClose={onClose} onCreated={onCreated} />);
    const submitBtn = screen.getByText("Create Case");
    expect(submitBtn).toBeDisabled();
  });

  it("submit button enables when title and message filled", () => {
    render(<CreateCaseModal onClose={onClose} onCreated={onCreated} />);
    fireEvent.change(screen.getByPlaceholderText(/brief summary/i), {
      target: { value: "My issue title" },
    });
    fireEvent.change(screen.getByPlaceholderText(/describe the issue/i), {
      target: { value: "Full description of the problem" },
    });
    const submitBtn = screen.getByText("Create Case");
    expect(submitBtn).not.toBeDisabled();
  });

  it("shows source dropdown with web selected by default", () => {
    render(<CreateCaseModal onClose={onClose} onCreated={onCreated} />);
    const sourceSelect = screen.getByText("web");
    expect(sourceSelect).toBeInTheDocument();
  });
});
