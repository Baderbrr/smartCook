import { Hourglass } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";
import { useI18n } from "../i18n.jsx";
import { daysUntil, useDebounced } from "../hooks.js";
import RecipeCard from "../components/RecipeCard.jsx";
import RecipeFilters, { EMPTY_FILTERS } from "../components/RecipeFilters.jsx";

const EXPIRING_WITHIN_DAYS = 3;

export default function SuggestionsPage() {
  const { t, lang } = useI18n();
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const q = useDebounced(filters.q);
  const [pantry, setPantry] = useState(null);
  const [suggestions, setSuggestions] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/pantry").then(setPantry).catch((e) => setError(e.message));
  }, [lang]);

  useEffect(() => {
    let cancelled = false;
    api("/recipes/suggestions", { params: { ...filters, q } })
      .then((data) => !cancelled && setSuggestions(data))
      .catch((e) => !cancelled && setError(e.message));
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lang, q, filters.category, filters.difficulty, filters.max_time, filters.max_missing, filters.tag]);

  const onFavoriteChange = (id, value) =>
    setSuggestions((list) => list.map((r) => (r.id === id ? { ...r, is_favorite: value } : r)));

  const expiring = (pantry ?? []).filter(
    (p) => p.expires_at && daysUntil(p.expires_at) <= EXPIRING_WITHIN_DAYS,
  );

  if (pantry && pantry.length === 0) {
    return (
      <div className="page">
        <h1>{t("suggestions.title")}</h1>
        <div className="empty card">
          <p>{t("suggestions.emptyPantry")}</p>
          <Link to="/pantry" className="btn btn-primary">{t("suggestions.goToPantry")}</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <h1>{t("suggestions.title")}</h1>
      <p className="muted">{t("suggestions.subtitle")}</p>

      {expiring.length > 0 && (
        <div className="alert alert-warning alert-icon">
          <Hourglass size={18} aria-hidden="true" />
          {t("suggestions.expiringBanner", { list: expiring.map((p) => p.ingredient.name).join(", ") })}
        </div>
      )}

      <RecipeFilters value={filters} onChange={setFilters} showMaxMissing />

      {error && <div className="alert alert-error">{error}</div>}
      {suggestions === null ? (
        <p className="muted">{t("common.loading")}</p>
      ) : suggestions.length === 0 ? (
        <p className="empty card">{t("suggestions.noResults")}</p>
      ) : (
        <div className="grid">
          {suggestions.map((recipe) => (
            <RecipeCard
              key={recipe.id}
              recipe={recipe}
              match={recipe.match}
              onFavoriteChange={onFavoriteChange}
            />
          ))}
        </div>
      )}
    </div>
  );
}
