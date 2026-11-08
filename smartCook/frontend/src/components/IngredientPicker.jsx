import { useId, useMemo, useState } from "react";
import { useI18n } from "../i18n.jsx";

const MAX_RESULTS = 8;

/** Autocomplete over the ingredient list; calls onSelect(ingredient) when one is picked. */
export default function IngredientPicker({ ingredients, excludeIds = new Set(), selected, onSelect }) {
  const { t } = useI18n();
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const listId = useId();

  const results = useMemo(() => {
    const needle = query.trim().toLocaleLowerCase();
    return ingredients
      .filter((i) => !i.is_staple && !excludeIds.has(i.id))
      .filter((i) => !needle || i.name.toLocaleLowerCase().includes(needle))
      .slice(0, MAX_RESULTS);
  }, [ingredients, excludeIds, query]);

  const pick = (ingredient) => {
    onSelect(ingredient);
    setQuery("");
    setOpen(false);
  };

  const onKeyDown = (e) => {
    if (!open && (e.key === "ArrowDown" || e.key === "Enter")) {
      setOpen(true);
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((a) => Math.min(a + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((a) => Math.max(a - 1, 0));
    } else if (e.key === "Enter" && results[active]) {
      e.preventDefault();
      pick(results[active]);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  if (selected) {
    return (
      <div className="picker-selected">
        <span className="chip chip-strong">{selected.name}</span>
        <button type="button" className="link-btn" onClick={() => onSelect(null)}>
          {t("common.edit")}
        </button>
      </div>
    );
  }

  return (
    <div className="picker">
      <input
        type="text"
        className="input"
        role="combobox"
        aria-expanded={open}
        aria-controls={listId}
        aria-autocomplete="list"
        placeholder={t("pantry.searchPlaceholder")}
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setActive(0);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        onKeyDown={onKeyDown}
      />
      {open && results.length > 0 && (
        <ul className="picker-list" id={listId} role="listbox">
          {results.map((ing, index) => (
            <li
              key={ing.id}
              role="option"
              aria-selected={index === active}
              className={index === active ? "active" : ""}
              onMouseDown={(e) => {
                e.preventDefault();
                pick(ing);
              }}
              onMouseEnter={() => setActive(index)}
            >
              <span>{ing.name}</span>
              <span className="muted small">{t(`ingredientCategory.${ing.category}`)}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
