import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { setApiLanguage } from "./api.js";
import { translations } from "./translations.js";

const LANG_KEY = "smartcook_lang";
const LOCALES = { pl: "pl-PL", en: "en-GB" };

const I18nContext = createContext(null);

function initialLang() {
  try {
    const saved = localStorage.getItem(LANG_KEY);
    if (saved in translations) return saved;
  } catch {
    // ignore unavailable storage
  }
  return navigator.language?.toLowerCase().startsWith("pl") ? "pl" : "en";
}

function lookup(lang, key) {
  return key.split(".").reduce((node, part) => node?.[part], translations[lang]);
}

export function I18nProvider({ children }) {
  const [lang, setLangState] = useState(initialLang);
  // Set synchronously so the very first requests from child effects use the right language.
  setApiLanguage(lang);

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  const setLang = useCallback((next) => {
    setLangState(next);
    try {
      localStorage.setItem(LANG_KEY, next);
    } catch {
      // ignore unavailable storage
    }
  }, []);

  const value = useMemo(() => {
    const locale = LOCALES[lang];
    const plural = new Intl.PluralRules(locale);
    const numberFormat = new Intl.NumberFormat(locale, { maximumFractionDigits: 2 });
    const dateFormat = new Intl.DateTimeFormat(locale, { day: "numeric", month: "short", year: "numeric" });

    const t = (key, vars) => {
      const text = lookup(lang, key);
      if (typeof text !== "string") return key;
      return text.replace(/\{(\w+)\}/g, (_, name) => vars?.[name] ?? `{${name}}`);
    };

    // A unit label agreeing with the number, e.g. "1 ząbek", "2 ząbki", "5 ząbków".
    const unitLabel = (code, quantity = 1) => {
      const forms = lookup(lang, `unit.${code}`);
      if (forms === undefined) return code ?? "";
      if (typeof forms === "string") return forms;
      return forms[plural.select(quantity)] ?? forms.other;
    };

    const formatQuantity = (quantity, unit) => {
      if (quantity === null || quantity === undefined) {
        return unit === "pinch" ? t("recipe.toTaste") : "";
      }
      return `${numberFormat.format(quantity)} ${unitLabel(unit, quantity)}`.trim();
    };

    const formatDate = (iso) => dateFormat.format(new Date(`${iso}T00:00:00`));

    return { lang, setLang, t, unitLabel, formatQuantity, formatDate };
  }, [lang, setLang]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  return useContext(I18nContext);
}
