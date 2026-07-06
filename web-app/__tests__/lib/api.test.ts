import { api, fetchCases, updateCaseStatus, addNote } from "@/lib/api";
import { jest } from "@jest/globals";

// Mock the axios instance directly
jest.mock("axios", () => {
  const mAxiosInstance = {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    patch: jest.fn(),
    delete: jest.fn(),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
  };
  return {
    create: jest.fn(() => mAxiosInstance),
  };
});

describe("API Client", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("fetchCases calls GET /cases", async () => {
    (api.get as jest.Mock).mockResolvedValueOnce({ data: { items: [] } });
    const result = await fetchCases({});
    expect(api.get).toHaveBeenCalledWith("/cases", { params: {} });
    expect(result).toEqual({ items: [] });
  });

  it("updateCaseStatus calls PATCH /cases/:id/status", async () => {
    (api.patch as jest.Mock).mockResolvedValueOnce({ data: { success: true } });
    const result = await updateCaseStatus("case-123", "resolved");
    expect(api.patch).toHaveBeenCalledWith("/cases/case-123/status", { status: "resolved" });
    expect(result.success).toBe(true);
  });

  it("addNote calls POST /cases/:id/notes", async () => {
    (api.post as jest.Mock).mockResolvedValueOnce({ data: { id: "note-1" } });
    const result = await addNote("case-123", "My note text");
    expect(api.post).toHaveBeenCalledWith("/cases/case-123/notes", { text: "My note text", is_internal: false });
    expect(result.id).toBe("note-1");
  });
});
