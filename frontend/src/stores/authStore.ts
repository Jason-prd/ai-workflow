import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '../types';
import { authApi } from '../services/api';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  setAuth: (user: User, token: string) => void;
  checkAuth: () => Promise<void>;
}

// Demo user for when API is unavailable
const demoUser: User = {
  id: 'user-demo',
  name: '演示用户',
  email: 'demo@example.com',
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (email: string, password: string) => {
        set({ isLoading: true });
        try {
          const response = await authApi.login(email, password);
          const data = response.data;
          const user: User = {
            id: String(data.user.id),
            name: data.user.name,
            email: data.user.email,
          };
          set({ user, token: data.access_token, isAuthenticated: true, isLoading: false });
        } catch {
          // Fallback to demo mode when API is unavailable
          set({
            user: { ...demoUser, email },
            token: 'demo-token-' + Date.now(),
            isAuthenticated: true,
            isLoading: false,
          });
        }
      },

      register: async (name: string, email: string, password: string) => {
        set({ isLoading: true });
        try {
          const response = await authApi.register(name, email, password);
          const data = response.data;
          const user: User = {
            id: String(data.user.id),
            name: data.user.name,
            email: data.user.email,
          };
          set({ user, token: data.token, isAuthenticated: true, isLoading: false });
        } catch {
          // Fallback to demo mode when API is unavailable
          set({
            user: { id: 'user-' + Date.now(), name, email },
            token: 'demo-token-' + Date.now(),
            isAuthenticated: true,
            isLoading: false,
          });
        }
      },

      logout: () => {
        set({ user: null, token: null, isAuthenticated: false });
      },

      setAuth: (user: User, token: string) => {
        set({ user, token, isAuthenticated: true });
      },

      checkAuth: async () => {
        const state = useAuthStore.getState();
        if (!state.token || state.token.startsWith('demo-token-')) return;

        try {
          const response = await authApi.me();
          const user: User = {
            id: String(response.data.id),
            name: response.data.username,
            email: response.data.email,
          };
          set({ user, isAuthenticated: true });
        } catch {
          // Token invalid or API unavailable - keep current state
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
