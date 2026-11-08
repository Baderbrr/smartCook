import { ArrowRight, PackagePlus } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";
import { useI18n } from "../i18n.jsx";
import IngredientPicker from "../components/IngredientPicker.jsx";
import UnitSelect from "../components/UnitSelect.jsx";

const EMPTY_FORM = { ingredient: null, quantity: "", unit: "" };

export default function ShoppingListPage() {
  const { t, lang, formatQuantity } = useI18n();
  const [items, setItems] = useState(null);
  const [ingredients, setIngredients] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = () => api("/shopping-list").then(setItems).catch((e) => setError(e.message));

  useEffect(() => {
    load();
    api("/ingredients").then(setIngredients).catch((e) => setError(e.message));
  }, [lang]);

  const checkedCount = useMemo(() => (items ?? []).filter((i) => i.checked).length, [items]);

  const run = async (fn) => {
    setError("");
    setNotice("");
    try {
      await fn();
    } catch (e) {
      setError(e.message);
    }
  };

  const add = (e) => {
    e.preventDefault();
    if (!form.ingredient) return;
    run(async () => {
      const list = await api("/shopping-list", {
        method: "POST",
        body: {
          ingredient_id: form.ingredient.id,
          quantity: form.quantity === "" ? null : Number(form.quantity),
          unit: form.quantity === "" ? null : form.unit,
        },
      });
      setItems(list);
      setForm(EMPTY_FORM);
    });
  };

  const toggle = (item) =>
    run(async () => {
      const updated = await api(`/shopping-list/${item.id}`, { method: "PATCH", body: { checked: !item.checked } });
      setItems((list) => list.map((i) => (i.id === updated.id ? updated : i)));
    });

  const remove = (item) =>
    run(async () => {
      await api(`/shopping-list/${item.id}`, { method: "DELETE" });
      setItems((list) => list.filter((i) => i.id !== item.id));
    });

  const moveToPantry = () =>
    run(async () => {
      await api("/shopping-list/checked/to-pantry", { method: "POST" });
      await load();
      setNotice(t("shopping.movedToPantry"));
    });

  const clearChecked = () =>
    run(async () => {
      await api("/shopping-list/checked", { method: "DELETE" });
      setItems((list) => list.filter((i) => !i.checked));
    });

  return (
    <div className="page">
      <h1>{t("shopping.title")}</h1>
      <p className="muted">{t("shopping.subtitle")}</p>

      <form className="card add-form" onSubmit={add}>
        <h2>{t("shopping.addTitle")}</h2>
        <div className="add-form-grid shopping">
          <div className="field">
            <IngredientPicker
              ingredients={ingredients}
              selected={form.ingredient}
              onSelect={(ingredient) => setForm({ ...EMPTY_FORM, ingredient, unit: ingredient?.default_unit ?? "" })}
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
          <button type="submit" className="btn btn-primary" disabled={!form.ingredient}>
            {t("common.add")}
          </button>
        </div>
      </form>

      {error && <div className="alert alert-error">{error}</div>}
      {notice && (
        <div className="alert alert-success">
          {notice}{" "}
          <Link to="/pantry" className="icon-link">
            {t("nav.pantry")} <ArrowRight size={16} aria-hidden="true" />
          </Link>
        </div>
      )}

      {items === null ? (
        <p className="muted">{t("common.loading")}</p>
      ) : items.length === 0 ? (
        <p className="empty card">{t("shopping.empty")}</p>
      ) : (
        <section className="card">
          <ul className="shopping-list">
            {items.map((item) => (
              <li key={item.id} className={item.checked ? "checked" : ""}>
                <label className="check">
                  <input type="checkbox" checked={item.checked} onChange={() => toggle(item)} />
                  <span className="row-name">{item.ingredient.name}</span>
                </label>
                <span className="muted">{formatQuantity(item.quantity, item.unit)}</span>
                {item.recipe_title ? (
                  <Link to={`/recipes/${item.recipe_id}`} className="small muted">
                    {t("shopping.forRecipe", { title: item.recipe_title })}
                  </Link>
                ) : (
                  <span />
                )}
                <button type="button" className="btn btn-ghost btn-sm danger" onClick={() => remove(item)}>
                  {t("common.delete")}
                </button>
              </li>
            ))}
          </ul>
          {checkedCount > 0 && (
            <div className="actions">
              <button type="button" className="btn btn-primary" onClick={moveToPantry}>
                <PackagePlus size={18} aria-hidden="true" /> {t("shopping.moveToPantry")} ({checkedCount})
              </button>
              <button type="button" className="btn btn-ghost" onClick={clearChecked}>
                {t("shopping.clearChecked")}
              </button>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
