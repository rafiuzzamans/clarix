import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

const API_BASE = 'http://10.0.2.2:80'; // Android emulator → host machine

export const api = axios.create({
  baseURL: API_BASE,
  headers: {'Content-Type': 'application/json'},
  timeout: 10000,
});

// Attach token
api.interceptors.request.use(async config => {
  const token = await AsyncStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto-refresh on 401
api.interceptors.response.use(
  res => res,
  async error => {
    if (error.response?.status === 401 && !error.config._retry) {
      error.config._retry = true;
      try {
        const refresh = await AsyncStorage.getItem('refresh_token');
        const {data} = await axios.post(`${API_BASE}/api/auth/refresh`, {refresh_token: refresh});
        await AsyncStorage.setItem('access_token', data.access_token);
        error.config.headers.Authorization = `Bearer ${data.access_token}`;
        return api(error.config);
      } catch {
        await AsyncStorage.multiRemove(['access_token', 'refresh_token', 'user']);
      }
    }
    return Promise.reject(error);
  },
);

// Auth
export const authApi = {
  login:   (email: string, password: string, mfa_code?: string) =>
    api.post('/api/auth/login', {email, password, mfa_code}),
  refresh: (refresh_token: string) =>
    api.post('/api/auth/refresh', {refresh_token}),
  logout:  (refresh_token: string) =>
    api.post('/api/auth/logout', {refresh_token}),
  me:      () => api.get('/api/auth/me'),
};

// Cases
export const casesApi = {
  list:     (params?: Record<string, any>) => api.get('/api/cases', {params}),
  get:      (id: string) => api.get(`/api/cases/${id}`),
  create:   (data: any)  => api.post('/api/cases', data),
  update:   (id: string, data: any) => api.patch(`/api/cases/${id}`, data),
  assign:   (id: string, agent_id: string) => api.post(`/api/cases/${id}/assign`, {agent_id}),
  escalate: (id: string, reason: string)   => api.post(`/api/cases/${id}/escalate`, {reason}),
  getNotes: (id: string) => api.get(`/api/cases/${id}/notes`),
  addNote:  (id: string, content: string, is_internal = true) =>
    api.post(`/api/cases/${id}/notes`, {content, is_internal}),
  getTimeline: (id: string) => api.get(`/api/cases/${id}/timeline`),
};

// Analytics
export const analyticsApi = {
  overview:         () => api.get('/api/analytics/overview'),
  caseVolume:       (days = 7) => api.get('/api/analytics/case-volume', {params: {days}}),
  agentPerformance: () => api.get('/api/analytics/agent-performance'),
  slaCompliance:    () => api.get('/api/analytics/sla-compliance'),
  priorityBreakdown: () => api.get('/api/analytics/priority-breakdown'),
};

// Notifications
export const notificationsApi = {
  inbox:    (userId: string) => api.get(`/api/notifications/inbox/${userId}`),
  markRead: (id: string)     => api.patch(`/api/notifications/read/${id}`),
};

// Chatbot
export const chatbotApi = {
  sendMessage: (session_id: string | null, message: string, user_id?: string) =>
    api.post('/api/chatbot/message', {session_id, message, user_id}),
};
