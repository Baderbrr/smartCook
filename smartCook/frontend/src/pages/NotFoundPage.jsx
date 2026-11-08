import { Link } from "react-router-dom";
import { useI18n } from "../i18n.jsx";

export default function NotFoundPage() {
  const { t } = useI18n();
  return (
    <div className="page empty">
      <h1>{t("notFound.title")}</h1>
      <Link to="/" className="btn btn-primary">{t("notFound.back")}</Link>
    </div>
  );
}
