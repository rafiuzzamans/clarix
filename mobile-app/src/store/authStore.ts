import {create} from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {authApi} from '../api';

interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'customer' | 'agent' | 'supervisor' | 'manager' | 'admin';
  status: string;
  mfa_enabled: boolean;
  department?: string;
}

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string, mfa_code?: string) => Promise<void>;
  logout: () => Promise<void>;
  loadUser: () => Promise<void>;
  isRole: (...roles: string[]) => boolean;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  loading: true,

  loadUser: async () => {
    set({loading: true});
    try {
      const token = await AsyncStorage.getItem('access_token');
      if (!token) {set({loading: false}); return;}
      const {data} = await authApi.me();
      set({user: data});
    } catch {
      await AsyncStorage.multiRemove(['access_token', 'refresh_token']);
      set({user: null});
    } finally {
      set({loading: false});
    }
  },

  login: async (email, password, mfa_code) => {
    const {data} = await authApi.login(email, password, mfa_code);
    await AsyncStorage.setItem('access_token', data.access_token);
    await AsyncStorage.setItem('refresh_token', data.refresh_token);
    set({user: data.user});
  },

  logout: async () => {
    try {
      const refresh = await AsyncStorage.getItem('refresh_token');
      if (refresh) await authApi.logout(refresh);
    } catch {}
    await AsyncStorage.multiRemove(['access_token', 'refresh_token']);
    set({user: null});
  },

  isRole: (...roles: string[]) => {
    const {user} = get();
    return user ? roles.includes(user.role) : false;
  },
}));
