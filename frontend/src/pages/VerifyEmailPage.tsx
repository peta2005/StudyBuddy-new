import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { BookOpen, Loader2 } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

export default function VerifyEmailPage() {
  const { verifyEmail, resendVerification } = useAuth();
  const [params] = useSearchParams();
  const token = params.get("token") || "";
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!token) return;

    let cancelled = false;
    const run = async () => {
      setSubmitting(true);
      const result = await verifyEmail(token);
      if (cancelled) return;
      if (result.error) setError(result.error);
      else setInfo(result.info || "Email verified.");
      setSubmitting(false);
    };
    run();

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const handleResend = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setInfo(null);
    setSubmitting(true);
    const result = await resendVerification(email.trim());
    if (result.error) setError(result.error);
    else setInfo(result.info || "Verification email sent.");
    setSubmitting(false);
  };

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-logo">
          <BookOpen size={20} />
        </div>
        <h1 className="auth-title">Verify your email</h1>

        {token ? (
          submitting ? (
            <Loader2 size={24} className="auth-spinner" />
          ) : (
            <>
              {error && <p className="auth-message auth-message--error">{error}</p>}
              {info && <p className="auth-message auth-message--info">{info}</p>}
            </>
          )
        ) : (
          <form className="auth-form" onSubmit={handleResend}>
            <p className="auth-subtitle">Enter your email to resend the verification link.</p>
            <input
              className="auth-input"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            {error && <p className="auth-message auth-message--error">{error}</p>}
            {info && <p className="auth-message auth-message--info">{info}</p>}
            <button className="auth-submit" type="submit" disabled={submitting}>
              {submitting ? <Loader2 size={16} className="auth-spinner" /> : "Resend email"}
            </button>
          </form>
        )}

        <Link className="auth-link auth-link--block" to="/">
          Back to sign in
        </Link>
      </div>
    </div>
  );
}
