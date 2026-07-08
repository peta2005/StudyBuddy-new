import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import type { AuthUser, AuthSession, AuthResult } from "@/types/auth";
import {
  login,
  register,
  refreshSession,
  fetchMe,
  forgotPassword as apiForgotPassword,
  resetPassword as apiResetPassword,
  verifyEmail as apiVerifyEmail,
  resendVerification as apiResendVerification,
  getOAuthUrl,
  getStoredSession,
  storeSession,
} from "@/lib/authApi";

interface AuthContextValue {
  session: AuthSession | null;
  user: AuthUser | null;
  accessToken: string | null;
  loading: boolean;
  configured: boolean;
  signIn: (email: string, password: string) => Promise<AuthResult>;
  signUp: (email: string, password: string) => Promise<AuthResult>;
  signOut: () => Promise<void>;
  forgotPassword: (email: string) => Promise<AuthResult>;
  resetPassword: (token: string, password: string) => Promise<AuthResult>;
  verifyEmail: (token: string) => Promise<AuthResult>;
  resendVerification: (email: string) => Promise<AuthResult>;
  completeOAuthSession: (session: AuthSession) => void;
  oauthUrl: (provider: "google" | "github") => string;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<AuthSession | null>(null);
  const [loading, setLoading] = useState(true);

  const applySession = useCallback((s: AuthSession | null) => {
    storeSession(s);
    setSession(s);
  }, []);

  const sessionFromResponse = (data: any): AuthSession => ({
    access_token: data.access_token,
    refresh_token: data.refresh_token,
    user: data.user,
  });

  // Restore session on mount
  useEffect(() => {
    const stored = getStoredSession();
    if (!stored) {
      setLoading(false);
      return;
    }

    // Try to refresh the token to validate the session
    refreshSession(stored.refresh_token)
      .then((data) => {
        applySession(sessionFromResponse(data));
      })
      .catch(() => {
        // Refresh failed — try using the existing access token to fetch /me
        fetchMe(stored.access_token)
          .then((user) => {
            applySession({ ...stored, user });
          })
          .catch(() => {
            // Session is completely dead
            applySession(null);
          });
      })
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      session,
      user: session?.user ?? null,
      accessToken: session?.access_token ?? null,
      loading,
      configured: true,
      signIn: async (email, password) => {
        try {
          const data = await login(email, password);
          applySession(sessionFromResponse(data));
          return { error: null };
        } catch (error) {
          return {
            error: error instanceof Error ? error.message : "Sign in failed.",
          };
        }
      },
      signUp: async (email, password) => {
        try {
          const data = await register(email, password);
          if (data.email_verification_required) {
            return {
              error: null,
              emailVerificationRequired: true,
              info: data.message || "Check your email to verify your account.",
            };
          }
          // Auto-sign in if no email verification required
          if (data.access_token && data.user) {
            applySession(sessionFromResponse(data));
          }
          return { error: null, info: data.message };
        } catch (error) {
          return {
            error: error instanceof Error ? error.message : "Sign up failed.",
          };
        }
      },
      signOut: async () => {
        applySession(null);
      },
      forgotPassword: async (email) => {
        try {
          const data = await apiForgotPassword(email);
          return { error: null, info: data.message };
        } catch (error) {
          return {
            error:
              error instanceof Error ? error.message : "Request failed.",
          };
        }
      },
      resetPassword: async (token, password) => {
        try {
          const data = await apiResetPassword(token, password);
          applySession(sessionFromResponse(data));
          return {
            error: null,
            info: data.message || "Password updated. You are now signed in.",
          };
        } catch (error) {
          return {
            error: error instanceof Error ? error.message : "Reset failed.",
          };
        }
      },
      verifyEmail: async (token) => {
        try {
          const data = await apiVerifyEmail(token);
          applySession(sessionFromResponse(data));
          return {
            error: null,
            info: data.message || "Email verified successfully.",
          };
        } catch (error) {
          return {
            error: error instanceof Error ? error.message : "Verification failed.",
          };
        }
      },
      resendVerification: async (email) => {
        try {
          const data = await apiResendVerification(email);
          return { error: null, info: data.message };
        } catch (error) {
          return {
            error:
              error instanceof Error
                ? error.message
                : "Failed to resend verification.",
          };
        }
      },
      completeOAuthSession: (nextSession) => applySession(nextSession),
      oauthUrl: getOAuthUrl,
    }),
    [session, loading, applySession]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
