import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { BookOpen, Loader2 } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { fetchMe, storeSession } from "@/lib/authApi";

export default function OAuthCallbackPage() {
  const { completeOAuthSession } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check if backend redirected back with an error
    const backendError = params.get("error");
    if (backendError) {
      setError(decodeURIComponent(backendError));
      return;
    }

    const accessToken = params.get("access_token");
    const refreshToken = params.get("refresh_token");

    if (!accessToken || !refreshToken) {
      setError("OAuth sign-in failed. No tokens received.");
      return;
    }

    // Timeout guard — if fetchMe takes > 8s, show error
    const timeout = setTimeout(() => {
      setError("OAuth sign-in timed out. Please try again.");
    }, 8000);

    const finish = async () => {
      try {
        const user = await fetchMe(accessToken);
        clearTimeout(timeout);
        const session = {
          access_token: accessToken,
          refresh_token: refreshToken,
          user,
        };
        storeSession(session);
        completeOAuthSession(session);
        navigate("/", { replace: true });
      } catch {
        clearTimeout(timeout);
        setError("OAuth sign-in failed. Please try again.");
      }
    };

    finish();

    return () => clearTimeout(timeout);
  }, [params, completeOAuthSession, navigate]);

  if (error) {
    return (
      <div className="auth-shell">
        <div className="auth-card">
          <div className="auth-logo">
            <BookOpen size={20} />
          </div>
          <h1 className="auth-title">Sign-in Failed</h1>
          <p className="auth-message auth-message--error">{error}</p>
          <button
            className="auth-submit"
            style={{ marginTop: 16 }}
            onClick={() => navigate("/", { replace: true })}
          >
            Back to sign in
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-shell">
      <div className="auth-card" style={{ textAlign: "center" }}>
        <Loader2 size={28} className="auth-spinner" style={{ margin: "0 auto 12px" }} />
        <p style={{ fontSize: 13, color: "var(--text-muted)" }}>Completing sign-in…</p>
      </div>
    </div>
  );
}
