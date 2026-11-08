import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, getToken, onUnauthorized, setToken } from "./api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    onUnauthorized(logout);
    if (!getToken()) {
      setReady(true);
      return;
    }
    api("/auth/me")
      .then(setUser)
      .catch(logout)
      .finally(() => setReady(true));
  }, [logout]);

  const authenticate = useCallback(async (path, body) => {
    const res = await api(path, { method: "POST", body });
    setToken(res.access_token);
    setUser(res.user);
    return res.user;
  }, []);

  const value = useMemo(
    () => ({
      user,
      ready,
      login: (email, password) => authenticate("/auth/login", { email, password }),
      register: (data) => authenticate("/auth/register", data),
      logout,
    }),
    [user, ready, authenticate, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
