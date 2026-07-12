import { casesApi, apiClient } from "@/lib/api";
import { jest } from "@jest/globals";

// Mock the axios instance directly
jest.mock("@/lib/api", () => {
  const actualApi = jest.requireActual("@/lib/api");
  return {
    ...(actualApi as object),
    apiClient: {
      get: jest.fn(),
      post: jest.fn(),
      put: jest.fn(),
      patch: jest.fn(),
      delete: jest.fn(),
    },
  };
});

describe("casesApi", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("list calls GET /api/cases", async () => {
    (apiClient.get as jest.Mock).mockResolvedValueOnce({ data: { items: [] } });
    const result = await casesApi.list({});
    expect(apiClient.get).toHaveBeenCalledWith("/api/cases", { params: {} });
    // In actual implementation, we return the whole axios response
    expect(result).toEqual({ data: { items: [] } });
  });

  it("update calls PATCH /api/cases/:id", async () => {
    (apiClient.patch as jest.Mock).mockResolvedValueOnce({ data: { success: true } });
    const result = await casesApi.update("case-123", { status: "resolved" });
    expect(apiClient.patch).toHaveBeenCalledWith("/api/cases/case-123", { status: "resolved" });
    expect(result).toEqual({ data: { success: true } });
  });

  it("addNote calls POST /api/cases/:id/notes", async () => {
    (apiClient.post as jest.Mock).mockResolvedValueOnce({ data: { id: "note-1" } });
    const result = await casesApi.addNote("case-123", "My note text", false);
    expect(apiClient.post).toHaveBeenCalledWith("/api/cases/case-123/notes", { content: "My note text", is_internal: false });
    expect(result).toEqual({ data: { id: "note-1" } });
  });
});
