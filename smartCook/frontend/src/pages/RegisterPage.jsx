import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import { useI18n } from "../i18n.jsx";

export default function RegisterPage() {
  const { user, register } = useAuth();
  const { t } = useI18n();
  const navigate = useNavigate();
  const [form, setForm] = useState({ display_name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await register(form);
      navigate("/pantry", { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth-page">
      <form className="card auth-card" onSubmit={submit}>
        <h1>{t("auth.registerTitle")}</h1>
        {error && <div className="alert alert-error">{error}</div>}
        <label className="field">
          <span>{t("auth.displayName")}</span>
          <input className="input" autoComplete="given-name" required maxLength={100} value={form.display_name} onChange={set("display_name")} />
        </label>
        <label className="field">
          <span>{t("auth.email")}</span>
          <input type="email" className="input" autoComplete="email" required value={form.email} onChange={set("email")} />
        </label>
        <label className="field">
          <span>{t("auth.password")}</span>
          <input
            type="password"
            className="input"
            autoComplete="new-password"
            required
            minLength={8}
            maxLength={64}
            value={form.password}
            onChange={set("password")}
          />
          <small className="muted">{t("auth.passwordHint")}</small>
        </label>
        <button type="submit" className="btn btn-primary btn-block" disabled={busy}>
          {t("auth.submitRegister")}
        </button>
        <p className="small muted">
          {t("auth.haveAccount")} <Link to="/login">{t("nav.login")}</Link>
        </p>
      </form>
    </div>
  );
}
