import { useEffect, useState } from "react";
import { api } from "../api.js";
import { useI18n } from "../i18n.jsx";

export const EMPTY_FILTERS = { q: "", category: "", difficulty: "", max_time: "", tag: [], max_missing: "" };

const TIME_OPTIONS = [15, 30, 45, 60, 90];
const MISSING_OPTIONS = [1, 2, 3];

export default function RecipeFilters({ value, onChange, showMaxMissing = false }) {
  const { t } = useI18n();
  const [meta, setMeta] = useState({ categories: [], tags: [], difficulties: [] });

  useEffect(() => {
    api("/recipes/meta").then(setMeta).catch(() => {});
  }, []);

  const set = (key, v) => onChange({ ...value, [key]: v });
  const toggleTag = (tag) =>
    set("tag", value.tag.includes(tag) ? value.tag.filter((x) => x !== tag) : [...value.tag, tag]);
  const isDirty = JSON.stringify(value) !== JSON.stringify(EMPTY_FILTERS);

  return (
    <section className="filters card">
      <div className="filters-row">
        <input
          type="search"
          className="input filters-search"
          placeholder={t("filters.search")}
          value={value.q}
          onChange={(e) => set("q", e.target.value)}
          aria-label={t("filters.search")}
        />
        <label className="field-inline">
          <span>{t("filters.category")}</span>
          <select className="input" value={value.category} onChange={(e) => set("category", e.target.value)}>
            <option value="">{t("filters.all")}</option>
            {meta.categories.map((c) => (
              <option key={c} value={c}>{t(`category.${c}`)}</option>
            ))}
          </select>
        </label>
        <label className="field-inline">
          <span>{t("filters.difficulty")}</span>
          <select className="input" value={value.difficulty} onChange={(e) => set("difficulty", e.target.value)}>
            <option value="">{t("filters.all")}</option>
            {meta.difficulties.map((d) => (
              <option key={d} value={d}>{t(`difficulty.${d}`)}</option>
            ))}
          </select>
        </label>
        <label className="field-inline">
          <span>{t("filters.maxTime")}</span>
          <select className="input" value={value.max_time} onChange={(e) => set("max_time", e.target.value)}>
            <option value="">{t("filters.anyTime")}</option>
            {TIME_OPTIONS.map((n) => (
              <option key={n} value={n}>{t("filters.upTo", { n })}</option>
            ))}
          </select>
        </label>
        {showMaxMissing && (
          <label className="field-inline">
            <span>{t("filters.maxMissing")}</span>
            <select className="input" value={value.max_missing} onChange={(e) => set("max_missing", e.target.value)}>
              <option value="">{t("filters.anyMissing")}</option>
              <option value="0">{t("filters.missingNone")}</option>
              {MISSING_OPTIONS.map((n) => (
                <option key={n} value={n}>{t("filters.missingUpTo", { n })}</option>
              ))}
            </select>
          </label>
        )}
      </div>
      <div className="chips">
        {meta.tags.map((tag) => (
          <button
            key={tag}
            type="button"
            className={`chip chip-toggle ${value.tag.includes(tag) ? "active" : ""}`}
            aria-pressed={value.tag.includes(tag)}
            onClick={() => toggleTag(tag)}
          >
            {t(`tag.${tag}`)}
          </button>
        ))}
        {isDirty && (
          <button type="button" className="link-btn" onClick={() => onChange(EMPTY_FILTERS)}>
            {t("filters.clear")}
          </button>
        )}
      </div>
    </section>
  );
}
