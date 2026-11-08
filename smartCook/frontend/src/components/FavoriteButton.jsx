import { Heart } from "lucide-react";
import { useState } from "react";
import { api } from "../api.js";
import { useI18n } from "../i18n.jsx";

export default function FavoriteButton({ recipeId, isFavorite, onChange, className = "", withLabel = false }) {
  const { t } = useI18n();
  const [busy, setBusy] = useState(false);
  const label = isFavorite ? t("recipe.favoriteRemove") : t("recipe.favoriteAdd");

  const toggle = async () => {
    setBusy(true);
    try {
      await api(`/favorites/${recipeId}`, { method: isFavorite ? "DELETE" : "PUT" });
      onChange(!isFavorite);
    } finally {
      setBusy(false);
    }
  };

  return (
    <button
      type="button"
      className={`btn btn-ghost fav-btn ${isFavorite ? "is-fav" : ""} ${className}`}
      onClick={toggle}
      disabled={busy}
      aria-pressed={isFavorite}
      aria-label={label}
      title={label}
    >
      <Heart size={18} fill={isFavorite ? "currentColor" : "none"} aria-hidden="true" />
      {withLabel && <span>{label}</span>}
    </button>
  );
}
