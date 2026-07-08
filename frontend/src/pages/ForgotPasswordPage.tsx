import { useState } from "react";
import { Link } from "react-router-dom";
import { BookOpen, Loader2 } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

export default function ForgotPasswordPage() {
  const { forgotPassword } = useAuth();
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setInfo(null);
    setSubmitting(true);
    const result = await forgotPassword(email.trim());
    if (result.error) setError(result.error);
    else setInfo(result.info || "If an account exists, a reset link was sent.");
    setSubmitting(false);
  };

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-logo">
          <BookOpen size={20} />
        </div>
        <h1 className="auth-title">Reset password</h1>
        <p className="auth-subtitle">We&apos;ll email you a secure reset link</p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="auth-label" htmlFor="email">
            Email
          </label>
          <input
            id="email"
            className="auth-input"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          {error && <p className="auth-message auth-message--error">{error}</p>}
          {info && <p className="auth-message auth-message--info">{info}</p>}

          <button className="auth-submit" type="submit" disabled={submitting}>
            {submitting ? <Loader2 size={16} className="auth-spinner" /> : "Send reset link"}
          </button>
        </form>

        <Link className="auth-link auth-link--block" to="/">
          Back to sign in
        </Link>
      </div>
    </div>
  );
}
