import { useEffect, useState } from "react";
import { api } from "../api.js";
import { useI18n } from "../i18n.jsx";
import RecipeCard from "../components/RecipeCard.jsx";

export default function FavoritesPage() {
  const { t, lang } = useI18n();
  const [recipes, setRecipes] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/favorites").then(setRecipes).catch((e) => setError(e.message));
  }, [lang]);

  const onFavoriteChange = (id, value) => {
    if (!value) setRecipes((list) => list.filter((r) => r.id !== id));
  };

  return (
    <div className="page">
      <h1>{t("favorites.title")}</h1>
      {error && <div className="alert alert-error">{error}</div>}
      {recipes === null ? (
        <p className="muted">{t("common.loading")}</p>
      ) : recipes.length === 0 ? (
        <p className="empty card">{t("favorites.empty")}</p>
      ) : (
        <div className="grid">
          {recipes.map((recipe) => (
            <RecipeCard key={recipe.id} recipe={recipe} onFavoriteChange={onFavoriteChange} />
          ))}
        </div>
      )}
    </div>
  );
}
