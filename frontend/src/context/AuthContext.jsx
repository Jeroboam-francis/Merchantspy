import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api } from "../services/api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(Boolean(localStorage.getItem("airtel_access_token")));

  const logout = useCallback(() => {
    localStorage.removeItem("airtel_access_token");
    setUser(null);
  }, []);

  useEffect(() => {
    if (!localStorage.getItem("airtel_access_token")) return;
    api("/auth/me")
      .then((response) => response.json())
      .then(setUser)
      .catch(logout)
      .finally(() => setLoading(false));
  }, [logout]);

  const login = useCallback(async (email, password) => {
    const response = await api("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    const { access_token: token } = await response.json();
    localStorage.setItem("airtel_access_token", token);
    const profileResponse = await api("/auth/me");
    setUser(await profileResponse.json());
  }, []);

  const value = useMemo(() => ({ user, loading, login, logout }), [user, loading, login, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used within AuthProvider");
  return value;
}
