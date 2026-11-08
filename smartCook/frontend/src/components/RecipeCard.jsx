import { Clock, Hourglass } from "lucide-react";
import { Link } from "react-router-dom";
import { useI18n } from "../i18n.jsx";
import CategoryIcon from "./CategoryIcon.jsx";
import FavoriteButton from "./FavoriteButton.jsx";

function MatchSection({ match }) {
  const { t } = useI18n();
  const level = match.match_percent >= 100 ? "full" : match.match_percent >= 50 ? "mid" : "low";
  return (
    <div className="match">
      <div className="match-head">
        <span>{t("recipe.matched", { matched: match.matched_count, required: match.required_count })}</span>
        <strong>{match.match_percent}%</strong>
      </div>
      <div className="progress" aria-hidden="true">
        <div className={`progress-bar ${level}`} style={{ width: `${match.match_percent}%` }} />
      </div>
      {match.missing.length > 0 && (
        <p className="small">
          <span className="muted">{t("recipe.missing")}</span>{" "}
          {match.missing.map((i) => i.name).join(", ")}
        </p>
      )}
      {match.expiring_used.length > 0 && (
        <p className="small expiring-note">
          <Hourglass size={14} aria-hidden="true" className="inline-icon" /> {t("recipe.expiringUsed")} {match.expiring_used.map((i) => i.name).join(", ")}
        </p>
      )}
    </div>
  );
}

export default function RecipeCard({ recipe, match, onFavoriteChange }) {
  const { t } = useI18n();
  return (
    <article className="card recipe-card">
      <Link to={`/recipes/${recipe.id}`} className="recipe-card-link">
        <div className="recipe-thumb">
          <CategoryIcon category={recipe.category} />
        </div>
        <div className="recipe-card-body">
          <p className="eyebrow">{t(`category.${recipe.category}`)}</p>
          <h3>{recipe.title}</h3>
          <p className="muted clamp-2">{recipe.description}</p>
          <p className="meta">
            <Clock size={14} aria-hidden="true" className="inline-icon" />{" "}
            {t("common.minutes", { n: recipe.prep_time_minutes })} · {t(`difficulty.${recipe.difficulty}`)}
          </p>
        </div>
      </Link>
      {recipe.tags.length > 0 && (
        <div className="chips">
          {recipe.tags.map((tag) => (
            <span key={tag} className="chip">{t(`tag.${tag}`)}</span>
          ))}
        </div>
      )}
      {match && <MatchSection match={match} />}
      {onFavoriteChange && (
        <FavoriteButton
          className="card-fav"
          recipeId={recipe.id}
          isFavorite={recipe.is_favorite}
          onChange={(value) => onFavoriteChange(recipe.id, value)}
        />
      )}
    </article>
  );
}
