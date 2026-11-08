import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { useAuth } from "./auth.jsx";
import { useI18n } from "./i18n.jsx";
import Layout from "./components/Layout.jsx";
import FavoritesPage from "./pages/FavoritesPage.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import NotFoundPage from "./pages/NotFoundPage.jsx";
import PantryPage from "./pages/PantryPage.jsx";
import RecipeDetailPage from "./pages/RecipeDetailPage.jsx";
import RecipesPage from "./pages/RecipesPage.jsx";
import RegisterPage from "./pages/RegisterPage.jsx";
import ShoppingListPage from "./pages/ShoppingListPage.jsx";
import SuggestionsPage from "./pages/SuggestionsPage.jsx";

function RequireAuth({ children }) {
  const { user, ready } = useAuth();
  const { t } = useI18n();
  const location = useLocation();
  if (!ready) return <p className="muted">{t("common.loading")}</p>;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<RequireAuth><SuggestionsPage /></RequireAuth>} />
        <Route path="pantry" element={<RequireAuth><PantryPage /></RequireAuth>} />
        <Route path="recipes" element={<RecipesPage />} />
        <Route path="recipes/:id" element={<RecipeDetailPage />} />
        <Route path="favorites" element={<RequireAuth><FavoritesPage /></RequireAuth>} />
        <Route path="shopping-list" element={<RequireAuth><ShoppingListPage /></RequireAuth>} />
        <Route path="login" element={<LoginPage />} />
        <Route path="register" element={<RegisterPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
