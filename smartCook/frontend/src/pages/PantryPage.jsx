import { ArrowRight, Info } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";
import { useI18n } from "../i18n.jsx";
import { daysUntil, groupBy } from "../hooks.js";
import IngredientPicker from "../components/IngredientPicker.jsx";
import UnitSelect from "../components/UnitSelect.jsx";

const EXPIRING_WITHIN_DAYS = 3;
const EMPTY_FORM = { ingredient: null, quantity: "", unit: "", expires_at: "" };

function ExpiryBadge({ date }) {
  const { t, formatDate } = useI18n();
  if (!date) return null;
  const days = daysUntil(date);
  if (days < 0) return <span className="badge badge-danger">{t("pantry.expired")}</span>;
  if (days <= EXPIRING_WITHIN_DAYS) {
    return <span className="badge badge-warning">{t("pantry.expiringSoon", { date: formatDate(date) })}</span>;
  }
  return <span className="badge">{t("pantry.expiresOn", { date: formatDate(date) })}</span>;
}

function PantryRow({ item, onSaved, onDeleted, onError }) {
  const { t, formatQuantity } = useI18n();
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(null);

  const startEdit = () => {
    setDraft({
      quantity: item.quantity ?? "",
      unit: item.unit ?? item.ingredient.default_unit,
      expires_at: item.expires_at ?? "",
    });
    setEditing(true);
  };

  const save = async (e) => {
    e.preventDefault();
    try {
      const updated = await api(`/pantry/${item.id}`, {
        method: "PATCH",
        body: {
          quantity: draft.quantity === "" ? null : Number(draft.quantity),
          unit: draft.quantity === "" ? null : draft.unit,
          expires_at: draft.expires_at || null,
        },
      });
      onSaved(updated);
      setEditing(false);
    } catch (err) {
      onError(err.message);
    }
  };

  const remove = async () => {
    try {
      await api(`/pantry/${item.id}`, { method: "DELETE" });
      onDeleted(item.id);
    } catch (err) {
      onError(err.message);
    }
  };

  if (editing) {
    return (
      <li className="pantry-row editing">
        <form onSubmit={save} className="row-form">
          <strong className="row-name">{item.ingredient.name}</strong>
          <input
            type="number"
            min="0"
            step="any"
            className="input input-qty"
            value={draft.quantity}
            onChange={(e) => setDraft({ ...draft, quantity: e.target.value })}
            aria-label={t("pantry.quantity")}
          />
          <UnitSelect value={draft.unit} onChange={(unit) => setDraft({ ...draft, unit })} aria-label={t("pantry.unit")} />
          <input
            type="date"
            className="input"
            value={draft.expires_at}
            onChange={(e) => setDraft({ ...draft, expires_at: e.target.value })}
            aria-label={t("pantry.expiresAt")}
          />
          <button type="submit" className="btn btn-primary btn-sm">{t("common.save")}</button>
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => setEditing(false)}>
            {t("common.cancel")}
          </button>
        </form>
      </li>
    );
  }

  return (
    <li className="pantry-row">
      <span className="row-name">{item.ingredient.name}</span>
      <span className="row-qty muted">{formatQuantity(item.quantity, item.unit) || "—"}</span>
      <ExpiryBadge date={item.expires_at} />
      <span className="row-actions">
        <button type="button" className="btn btn-ghost btn-sm" onClick={startEdit}>{t("common.edit")}</button>
        <button type="button" className="btn btn-ghost btn-sm danger" onClick={remove}>{t("common.delete")}</button>
      </span>
    </li>
  );
}

export default function PantryPage() {
  const { t, lang } = useI18n();
  const [items, setItems] = useState(null);
  const [ingredients, setIngredients] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/pantry").then(setItems).catch((e) => setError(e.message));
    api("/ingredients").then(setIngredients).catch((e) => setError(e.message));
  }, [lang]);

  const ownedIds = useMemo(() => new Set((items ?? []).map((i) => i.ingredient.id)), [items]);
  const groups = useMemo(() => groupBy(items ?? [], (i) => i.ingredient.category), [items]);

  const selectIngredient = (ingredient) =>
    setForm({ ...EMPTY_FORM, ingredient, unit: ingredient?.default_unit ?? "" });

  const add = async (e) => {
    e.preventDefault();
    if (!form.ingredient) return;
    setError("");
    try {
      const created = await api("/pantry", {
        method: "POST",
        body: {
          ingredient_id: form.ingredient.id,
          quantity: form.quantity === "" ? null : Number(form.quantity),
          unit: form.quantity === "" ? null : form.unit,
          expires_at: form.expires_at || null,
        },
      });
      setItems((list) => [...list, created]);
      setForm(EMPTY_FORM);
    } catch (err) {
      setError(err.message);
    }
  };

  const replaceItem = (updated) => setItems((list) => list.map((i) => (i.id === updated.id ? updated : i)));
  const removeItem = (id) => setItems((list) => list.filter((i) => i.id !== id));

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>{t("pantry.title")}</h1>
          <p className="muted">{t("pantry.subtitle")}</p>
        </div>
        {items?.length > 0 && (
          <Link to="/" className="btn btn-primary">
            {t("pantry.goToSuggestions")} <ArrowRight size={18} aria-hidden="true" />
          </Link>
        )}
      </div>

      <form className="card add-form" onSubmit={add}>
        <h2>{t("pantry.addTitle")}</h2>
        <div className="add-form-grid">
          <div className="field">
            <IngredientPicker
              ingredients={ingredients}
              excludeIds={ownedIds}
              selected={form.ingredient}
              onSelect={selectIngredient}
            />
          </div>
          <label className="field">
            <span>{t("pantry.quantity")}</span>
            <input
              type="number"
              min="0"
              step="any"
              className="input"
              value={form.quantity}
              onChange={(e) => setForm({ ...form, quantity: e.target.value })}
            />
          </label>
          <label className="field">
            <span>{t("pantry.unit")}</span>
            <UnitSelect value={form.unit} onChange={(unit) => setForm({ ...form, unit })} />
          </label>
          <label className="field">
            <span>{t("pantry.expiresAt")}</span>
            <input
              type="date"
              className="input"
              value={form.expires_at}
              onChange={(e) => setForm({ ...form, expires_at: e.target.value })}
            />
          </label>
          <button type="submit" className="btn btn-primary" disabled={!form.ingredient}>
            {t("common.add")}
          </button>
        </div>
        <p className="small muted note-icon">
          <Info size={16} aria-hidden="true" /> {t("pantry.staplesNote")}
        </p>
      </form>

      {error && <div className="alert alert-error">{error}</div>}

      {items === null ? (
        <p className="muted">{t("common.loading")}</p>
      ) : items.length === 0 ? (
        <p className="empty card">{t("pantry.empty")}</p>
      ) : (
        <>
          <p className="muted small">{t("pantry.count", { n: items.length })}</p>
          <div className="pantry-groups">
            {groups.map(([category, groupItems]) => (
              <section key={category} className="card">
                <h3>{t(`ingredientCategory.${category}`)}</h3>
                <ul className="pantry-list">
                  {groupItems.map((item) => (
                    <PantryRow
                      key={item.id}
                      item={item}
                      onSaved={replaceItem}
                      onDeleted={removeItem}
                      onError={setError}
                    />
                  ))}
                </ul>
              </section>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
