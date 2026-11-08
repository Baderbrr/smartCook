import { ArrowLeft, Check, CircleCheck, Clock, Gauge, Minus, Plus, ShoppingCart, Users, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api.js";
import { useAuth } from "../auth.jsx";
import { useI18n } from "../i18n.jsx";
import CategoryIcon from "../components/CategoryIcon.jsx";
import FavoriteButton from "../components/FavoriteButton.jsx";

export default function RecipeDetailPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const { t, lang, formatQuantity } = useI18n();
  const navigate = useNavigate();
  const [recipe, setRecipe] = useState(null);
  const [servings, setServings] = useState(1);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  // Keep the user's servings choice across reloads of the same recipe, reset it for a new one.
  const loadedId = useRef(null);

  const load = () =>
    api(`/recipes/${id}`)
      .then((data) => {
        setError("");
        setRecipe(data);
        if (loadedId.current !== data.id) setServings(data.servings);
        loadedId.current = data.id;
      })
      .catch((e) => setError(e.status === 404 ? t("recipe.notFound") : e.message));

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, lang, user]);

  if (error) return <div className="alert alert-error">{error}</div>;
  if (!recipe) return <p className="muted">{t("common.loading")}</p>;

  const scale = servings / recipe.servings;
  const missingCount = recipe.match?.missing.length ?? 0;

  const run = async (fn) => {
    setBusy(true);
    setNotice("");
    setActionError("");
    try {
      await fn();
    } catch (e) {
      setActionError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const addMissing = () =>
    run(async () => {
      await api(`/shopping-list/from-recipe/${recipe.id}`, { method: "POST", params: { servings } });
      setNotice(t("recipe.addedMissing"));
    });

  const cook = () => {
    if (!window.confirm(t("recipe.cookConfirm"))) return;
    run(async () => {
      const res = await api(`/recipes/${recipe.id}/cook`, { method: "POST", params: { servings } });
      const parts = [t("recipe.cooked")];
      if (res.updated.length) parts.push(t("recipe.cookedUpdated", { list: res.updated.map((i) => i.name).join(", ") }));
      if (res.removed.length) parts.push(t("recipe.cookedRemoved", { list: res.removed.map((i) => i.name).join(", ") }));
      setNotice(parts.join(" "));
      await load();
    });
  };

  return (
    <div className="page recipe-detail">
      <button type="button" className="link-btn icon-link" onClick={() => navigate(-1)}>
        <ArrowLeft size={16} aria-hidden="true" /> {t("recipe.back")}
      </button>

      <header className="recipe-hero card">
        <div className="recipe-hero-icon">
          <CategoryIcon category={recipe.category} size={48} />
        </div>
        <div className="recipe-hero-body">
          <p className="eyebrow">{t(`category.${recipe.category}`)}</p>
          <h1>{recipe.title}</h1>
          <p className="muted">{recipe.description}</p>
          <p className="meta meta-icons">
            <span><Clock size={16} aria-hidden="true" /> {t("common.minutes", { n: recipe.prep_time_minutes })}</span>
            <span><Gauge size={16} aria-hidden="true" /> {t(`difficulty.${recipe.difficulty}`)}</span>
            <span><Users size={16} aria-hidden="true" /> {t("common.servings", { n: recipe.servings })}</span>
          </p>
          <div className="chips">
            {recipe.tags.map((tag) => (
              <span key={tag} className="chip">{t(`tag.${tag}`)}</span>
            ))}
          </div>
          {user && (
            <div className="actions">
              <FavoriteButton
                recipeId={recipe.id}
                isFavorite={recipe.is_favorite}
                onChange={(v) => setRecipe({ ...recipe, is_favorite: v })}
                withLabel
              />
              {missingCount > 0 && (
                <button type="button" className="btn btn-secondary" onClick={addMissing} disabled={busy}>
                  <ShoppingCart size={18} aria-hidden="true" /> {t("recipe.addMissing")}
                </button>
              )}
              <button type="button" className="btn btn-primary" onClick={cook} disabled={busy}>
                <CircleCheck size={18} aria-hidden="true" /> {t("recipe.cook")}
              </button>
            </div>
          )}
        </div>
      </header>

      {notice && <div className="alert alert-success">{notice}</div>}
      {actionError && <div className="alert alert-error">{actionError}</div>}

      <div className="recipe-columns">
        <section className="card">
          <div className="section-head">
            <h2>{t("recipe.ingredients")}</h2>
            <label className="servings-control">
              <span>{t("recipe.servings")}</span>
              <button type="button" className="btn btn-ghost btn-icon" onClick={() => setServings((s) => Math.max(1, s - 1))} aria-label="−">
                <Minus size={16} aria-hidden="true" />
              </button>
              <strong>{servings}</strong>
              <button type="button" className="btn btn-ghost btn-icon" onClick={() => setServings((s) => s + 1)} aria-label="+">
                <Plus size={16} aria-hidden="true" />
              </button>
            </label>
          </div>

          {!user && (
            <p className="small muted">
              <Link to="/login">{t("recipe.loginToSeeMatch")}</Link>
            </p>
          )}
          {user && recipe.match && missingCount === 0 && (
            <p className="alert alert-success small">{t("recipe.allAvailable")}</p>
          )}

          <ul className="ingredient-list">
            {recipe.ingredients.map((ri) => {
              const qty = ri.quantity === null ? null : ri.quantity * scale;
              const status = ri.available === null ? "" : ri.available ? "have" : ri.optional ? "optional" : "missing";
              return (
                <li key={ri.ingredient.id} className={status}>
                  {ri.available !== null && (
                    <span
                      className="status-icon"
                      title={ri.available ? t("recipe.have") : t("recipe.dontHave")}
                      aria-label={ri.available ? t("recipe.have") : t("recipe.dontHave")}
                    >
                      {ri.available ? <Check size={16} strokeWidth={3} /> : <X size={16} strokeWidth={3} />}
                    </span>
                  )}
                  <span className="ing-name">
                    {ri.ingredient.name}
                    {ri.optional && <span className="muted small"> ({t("recipe.optional")})</span>}
                  </span>
                  <span className="ing-qty">{formatQuantity(qty, ri.unit)}</span>
                </li>
              );
            })}
          </ul>
        </section>

        <section className="card">
          <h2>{t("recipe.steps")}</h2>
          <ol className="steps">
            {recipe.steps.map((step, index) => (
              <li key={index}>{step}</li>
            ))}
          </ol>
        </section>
      </div>
    </div>
  );
}
