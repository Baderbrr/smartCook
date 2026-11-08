import { useEffect, useState } from "react";
import { api } from "../api.js";
import { useAuth } from "../auth.jsx";
import { useI18n } from "../i18n.jsx";
import { useDebounced } from "../hooks.js";
import RecipeCard from "../components/RecipeCard.jsx";
import RecipeFilters, { EMPTY_FILTERS } from "../components/RecipeFilters.jsx";

export default function RecipesPage() {
  const { t, lang } = useI18n();
  const { user } = useAuth();
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const q = useDebounced(filters.q);
  const [recipes, setRecipes] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    const { max_missing: _ignored, ...params } = filters;
    api("/recipes", { params: { ...params, q } })
      .then((data) => !cancelled && setRecipes(data))
      .catch((e) => !cancelled && setError(e.message));
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lang, user, q, filters.category, filters.difficulty, filters.max_time, filters.tag]);

  const onFavoriteChange = (id, value) =>
    setRecipes((list) => list.map((r) => (r.id === id ? { ...r, is_favorite: value } : r)));

  return (
    <div className="page">
      <h1>{t("recipes.title")}</h1>
      <p className="muted">{t("recipes.subtitle")}</p>
      <RecipeFilters value={filters} onChange={setFilters} />
      {error && <div className="alert alert-error">{error}</div>}
      {recipes === null ? (
        <p className="muted">{t("common.loading")}</p>
      ) : recipes.length === 0 ? (
        <p className="empty card">{t("recipes.empty")}</p>
      ) : (
        <div className="grid">
          {recipes.map((recipe) => (
            <RecipeCard
              key={recipe.id}
              recipe={recipe}
              onFavoriteChange={user ? onFavoriteChange : undefined}
            />
          ))}
        </div>
      )}
    </div>
  );
}
