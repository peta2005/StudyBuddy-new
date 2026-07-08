import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { BookOpen, Loader2 } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

export default function ResetPasswordPage() {
  const { resetPassword } = useAuth();
  const [params] = useSearchParams();
  const token = params.get("token") || "";
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setInfo(null);

    if (!token) {
      setError("Missing reset token. Open the link from your email.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }

    setSubmitting(true);
    const result = await resetPassword(token, password);
    if (result.error) setError(result.error);
    else setInfo(result.info || "Password updated.");
    setSubmitting(false);
  };

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-logo">
          <BookOpen size={20} />
        </div>
        <h1 className="auth-title">Choose a new password</h1>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="auth-label" htmlFor="password">
            New password
          </label>
          <input
            id="password"
            className="auth-input"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={8}
            required
          />

          <label className="auth-label" htmlFor="confirm">
            Confirm password
          </label>
          <input
            id="confirm"
            className="auth-input"
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            minLength={8}
            required
          />

          {error && <p className="auth-message auth-message--error">{error}</p>}
          {info && <p className="auth-message auth-message--info">{info}</p>}

          <button className="auth-submit" type="submit" disabled={submitting}>
            {submitting ? <Loader2 size={16} className="auth-spinner" /> : "Update password"}
          </button>
        </form>

        <Link className="auth-link auth-link--block" to="/">
          Back to sign in
        </Link>
      </div>
    </div>
  );
}
