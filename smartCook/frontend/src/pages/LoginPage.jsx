import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import { useI18n } from "../i18n.jsx";

export default function LoginPage() {
  const { user, login } = useAuth();
  const { t } = useI18n();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(email, password);
      navigate(location.state?.from ?? "/", { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth-page">
      <form className="card auth-card" onSubmit={submit}>
        <h1>{t("auth.loginTitle")}</h1>
        {error && <div className="alert alert-error">{error}</div>}
        <label className="field">
          <span>{t("auth.email")}</span>
          <input
            type="email"
            className="input"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>
        <label className="field">
          <span>{t("auth.password")}</span>
          <input
            type="password"
            className="input"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        <button type="submit" className="btn btn-primary btn-block" disabled={busy}>
          {t("auth.submitLogin")}
        </button>
        <p className="small muted">
          {t("auth.noAccount")} <Link to="/register">{t("nav.register")}</Link>
        </p>
        <p className="small muted demo-hint">{t("auth.demoHint")}</p>
      </form>
    </div>
  );
}
