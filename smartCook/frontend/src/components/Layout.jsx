import { ChefHat } from "lucide-react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import { useI18n } from "../i18n.jsx";

export default function Layout() {
  const { user, logout } = useAuth();
  const { t, lang, setLang } = useI18n();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <>
      <header className="header">
        <div className="header-inner">
          <NavLink to={user ? "/" : "/recipes"} className="logo">
            <ChefHat size={24} strokeWidth={2} aria-hidden="true" /> SmartCook
          </NavLink>
          <nav className="nav">
            {user && <NavLink to="/" end>{t("nav.suggestions")}</NavLink>}
            {user && <NavLink to="/pantry">{t("nav.pantry")}</NavLink>}
            <NavLink to="/recipes">{t("nav.recipes")}</NavLink>
            {user && <NavLink to="/favorites">{t("nav.favorites")}</NavLink>}
            {user && <NavLink to="/shopping-list">{t("nav.shopping")}</NavLink>}
          </nav>
          <div className="header-actions">
            <div className="lang-switch" role="group" aria-label={t("nav.language")}>
              {["pl", "en"].map((code) => (
                <button
                  key={code}
                  type="button"
                  className={lang === code ? "active" : ""}
                  aria-pressed={lang === code}
                  onClick={() => setLang(code)}
                >
                  {code.toUpperCase()}
                </button>
              ))}
            </div>
            {user ? (
              <>
                <span className="user-name">{user.display_name}</span>
                <button type="button" className="btn btn-ghost btn-sm" onClick={handleLogout}>
                  {t("nav.logout")}
                </button>
              </>
            ) : (
              <>
                <NavLink to="/login" className="btn btn-ghost btn-sm">{t("nav.login")}</NavLink>
                <NavLink to="/register" className="btn btn-primary btn-sm">{t("nav.register")}</NavLink>
              </>
            )}
          </div>
        </div>
      </header>
      <main className="container">
        <Outlet />
      </main>
    </>
  );
}
