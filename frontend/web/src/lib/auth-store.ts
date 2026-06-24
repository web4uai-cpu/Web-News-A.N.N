import { create } from "zustand";
import { auth } from "./firebase";
import {
  onAuthStateChanged,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut as firebaseSignOut,
  sendPasswordResetEmail,
  type User,
} from "firebase/auth";

interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;

  initialize: () => void;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  loading: true,
  error: null,

  initialize: () => {
    onAuthStateChanged(auth, (user) => {
      set({ user, loading: false });
    });
  },

  signIn: async (email, password) => {
    set({ error: null });
    try {
      await signInWithEmailAndPassword(auth, email, password);
    } catch (e: unknown) {
      set({ error: (e as Error).message });
    }
  },

  signUp: async (email, password) => {
    set({ error: null });
    try {
      await createUserWithEmailAndPassword(auth, email, password);
    } catch (e: unknown) {
      set({ error: (e as Error).message });
    }
  },

  signOut: async () => {
    await firebaseSignOut(auth);
    set({ user: null });
  },

  resetPassword: async (email) => {
    set({ error: null });
    try {
      await sendPasswordResetEmail(auth, email);
      set({ error: "Reset link sent to your email." });
    } catch (e: unknown) {
      set({ error: (e as Error).message });
    }
  },

  clearError: () => set({ error: null }),
}));
