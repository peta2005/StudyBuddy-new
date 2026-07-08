import { useState, useEffect } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { BookOpen, Loader2 } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { getOAuthUrl } from "@/lib/authApi";

export const AuthPage = () => {
  const { signIn, signUp } = useAuth();
  const [searchParams] = useSearchParams();
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(
    searchParams.get("error") ? decodeURIComponent(searchParams.get("error")!) : null
  );
  const [info, setInfo] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Clear error from URL bar without re-mounting
  useEffect(() => {
    if (searchParams.get("error")) {
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setInfo(null);

    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setSubmitting(true);
    const result =
      mode === "signin"
        ? await signIn(email.trim(), password)
        : await signUp(email.trim(), password);

    if (result.error) {
      setError(result.error);
    } else if (result.emailVerificationRequired) {
      setInfo(result.info || "Check your email to verify your account, then sign in.");
      setMode("signin");
    } else if (result.info) {
      setInfo(result.info);
    }

    setSubmitting(false);
  };

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-logo">
          <BookOpen size={20} />
        </div>
        <h1 className="auth-title">Smart Study Buddy</h1>
        <p className="auth-subtitle">Sign in to access your private study workspace</p>

        <div className="auth-oauth-row">
          <a className="auth-oauth-btn" href={getOAuthUrl("google")}>
            Continue with Google
          </a>
        </div>

        <p className="auth-divider">or use email</p>

        <div className="auth-tabs">
          <button
            type="button"
            className={`auth-tab${mode === "signin" ? " auth-tab--active" : ""}`}
            onClick={() => setMode("signin")}
          >
            Sign in
          </button>
          <button
            type="button"
            className={`auth-tab${mode === "signup" ? " auth-tab--active" : ""}`}
            onClick={() => setMode("signup")}
          >
            Sign up
          </button>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="auth-label" htmlFor="email">
            Email
          </label>
          <input
            id="email"
            className="auth-input"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <label className="auth-label" htmlFor="password">
            Password
          </label>
          <input
            id="password"
            className="auth-input"
            type="password"
            autoComplete={mode === "signin" ? "current-password" : "new-password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={8}
            required
          />

          {mode === "signin" && (
            <Link className="auth-link" to="/forgot-password">
              Forgot password?
            </Link>
          )}

          {error && <p className="auth-message auth-message--error">{error}</p>}
          {info && <p className="auth-message auth-message--info">{info}</p>}

          <button className="auth-submit" type="submit" disabled={submitting}>
            {submitting ? (
              <>
                <Loader2 size={16} className="auth-spinner" />
                Please wait…
              </>
            ) : mode === "signin" ? (
              "Sign in"
            ) : (
              "Create account"
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default AuthPage;
