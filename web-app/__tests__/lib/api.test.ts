import { casesApi, apiClient } from "@/lib/api";
import { jest } from "@jest/globals";

// Mock the auth context token getter
jest.mock("@/lib/auth-context", () => ({
  __esModule: true,
  useAuth: () => ({ token: "fake-token" })
}));



describe("casesApi", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("list calls GET /api/cases", async () => {
    jest.spyOn(apiClient, 'get').mockResolvedValueOnce({ data: { items: [] } } as any);
    const result = await casesApi.list({});
    expect(apiClient.get).toHaveBeenCalledWith("/api/cases", { params: {} });
    // In actual implementation, we return the whole axios response
    expect(result).toEqual({ data: { items: [] } });
  });

  it("update calls PATCH /api/cases/:id", async () => {
    jest.spyOn(apiClient, 'patch').mockResolvedValueOnce({ data: { success: true } } as any);
    const result = await casesApi.update("case-123", { status: "resolved" });
    expect(apiClient.patch).toHaveBeenCalledWith("/api/cases/case-123", { status: "resolved" });
    expect(result).toEqual({ data: { success: true } });
  });

  it("addNote calls POST /api/cases/:id/notes", async () => {
    jest.spyOn(apiClient, 'post').mockResolvedValueOnce({ data: { id: "note-1" } } as any);
    const result = await casesApi.addNote("case-123", "My note text", false);
    expect(apiClient.post).toHaveBeenCalledWith("/api/cases/case-123/notes", { content: "My note text", is_internal: false });
    expect(result).toEqual({ data: { id: "note-1" } });
  });
});
