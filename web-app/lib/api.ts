import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:80";

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
});

// Attach access token to every request
apiClient.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-refresh on 401
apiClient.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      try {
        const refreshToken = localStorage.getItem("refresh_token");
        const { data } = await axios.post(`${API_BASE}/api/auth/refresh`, {
          refresh_token: refreshToken,
        });
        localStorage.setItem("access_token", data.access_token);
        original.headers.Authorization = `Bearer ${data.access_token}`;
        return apiClient(original);
      } catch {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

// ─── Auth
export const authApi = {
  login: (email: string, password: string, mfa_code?: string) =>
    apiClient.post("/api/auth/login", { email, password, mfa_code }),
  refresh: (refresh_token: string) =>
    apiClient.post("/api/auth/refresh", { refresh_token }),
  logout: (refresh_token: string) =>
    apiClient.post("/api/auth/logout", { refresh_token }),
  me: () => apiClient.get("/api/auth/me"),
};

// ─── Users
export const usersApi = {
  list: (params?: Record<string, unknown>) =>
    apiClient.get("/api/users", { params }),
  get: (id: string) => apiClient.get(`/api/users/${id}`),
  create: (data: unknown) => apiClient.post("/api/users", data),
  update: (id: string, data: unknown) => apiClient.patch(`/api/users/${id}`, data),
  updateRole: (id: string, role: string) =>
    apiClient.patch(`/api/users/${id}/role`, { role }),
  updateStatus: (id: string, status: string) =>
    apiClient.patch(`/api/users/${id}/status`, { status }),
  deactivate: (id: string) => apiClient.delete(`/api/users/${id}`),
};

// ─── Cases
export const casesApi = {
  list: (params?: Record<string, unknown>) =>
    apiClient.get("/api/cases", { params }),
  get: (id: string) => apiClient.get(`/api/cases/${id}`),
  create: (data: unknown) => apiClient.post("/api/cases", data),
  update: (id: string, data: unknown) => apiClient.patch(`/api/cases/${id}`, data),
  assign: (id: string, agent_id: string, team_id?: string) =>
    apiClient.post(`/api/cases/${id}/assign`, { agent_id, team_id }),
  escalate: (id: string, reason: string) =>
    apiClient.post(`/api/cases/${id}/escalate`, { reason }),
  getNotes: (id: string) => apiClient.get(`/api/cases/${id}/notes`),
  addNote: (id: string, content: string, is_internal = true) =>
    apiClient.post(`/api/cases/${id}/notes`, { content, is_internal }),
  getTimeline: (id: string) => apiClient.get(`/api/cases/${id}/timeline`),
};

// ─── AI
export const aiApi = {
  predict: (text: string) => apiClient.post("/api/ai/predict", { text }),
  status: () => apiClient.get("/api/ai/status"),
  train: () => apiClient.post("/api/ai/train"),
};

// ─── Chatbot
export const chatbotApi = {
  sendMessage: (session_id: string | null, message: string, user_id?: string) =>
    apiClient.post("/api/chatbot/message", { session_id, message, user_id }),
  getSession: (session_id: string) =>
    apiClient.get(`/api/chatbot/session/${session_id}`),
  searchFAQ: (q: string) =>
    apiClient.get("/api/chatbot/faq/search", { params: { q } }),
};

// ─── Analytics
export const analyticsApi = {
  overview: () => apiClient.get("/api/analytics/overview"),
  caseVolume: (days = 30) =>
    apiClient.get("/api/analytics/case-volume", { params: { days } }),
  sentimentTrend: (days = 30) =>
    apiClient.get("/api/analytics/sentiment-trend", { params: { days } }),
  priorityBreakdown: () => apiClient.get("/api/analytics/priority-breakdown"),
  categoryBreakdown: () => apiClient.get("/api/analytics/category-breakdown"),
  agentPerformance: () => apiClient.get("/api/analytics/agent-performance"),
  statusBreakdown: () => apiClient.get("/api/analytics/status-breakdown"),
  slaCompliance: () => apiClient.get("/api/analytics/sla-compliance"),
};

// ─── Notifications
export const notificationsApi = {
  inbox: (userId: string, unread_only = false) =>
    apiClient.get(`/api/notifications/inbox/${userId}`, { params: { unread_only } }),
  markRead: (id: string) => apiClient.patch(`/api/notifications/read/${id}`),
};

// ─── Files
export const filesApi = {
  upload: (formData: FormData) =>
    apiClient.post("/api/files/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  listForCase: (caseId: string) => apiClient.get(`/api/files/case/${caseId}`),
  delete: (fileId: string) => apiClient.delete(`/api/files/${fileId}`),
};

// ─── Audit
export const auditApi = {
  logs: (params?: Record<string, unknown>) =>
    apiClient.get("/api/audit/logs", { params }),
  byActor: (actorId: string) =>
    apiClient.get(`/api/audit/logs/actor/${actorId}`),
};

# Add analytics API client methods

# Add users API client

# Add knowledge base API client

# Retry failed requests once
