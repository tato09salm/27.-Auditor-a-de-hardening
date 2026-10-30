import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { authApi, ApiError, refreshAccessToken, setAccessToken, setAuthFailureHandler } from "../lib/api";
import { queryClient } from "../lib/queryClient";
import type { SetupStatus, User } from "../types";

type AuthStage = "loading" | "setup" | "login" | "authenticated" | "offline";

interface AuthContextValue {
  stage: AuthStage;
  user: User | null;
  setupStatus: SetupStatus | null;
  bootError: string | null;
  login: (email: string, password: string) => Promise<void>;
  initialize: (payload: {
    organization_name: string;
    organization_slug: string;
    admin_full_name: string;
    admin_email: string;
    admin_password: string;
  }) => Promise<void>;
  logout: () => Promise<void>;
  retryBoot: () => void;
  refreshUser: () => Promise<void>;
  hasPermission: (code: string) => boolean;
  hasAnyPermission: (...codes: string[]) => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [stage, setStage] = useState<AuthStage>("loading");
  const [user, setUser] = useState<User | null>(null);
  const [setupStatus, setSetupStatus] = useState<SetupStatus | null>(null);
  const [bootError, setBootError] = useState<string | null>(null);
  const [bootAttempt, setBootAttempt] = useState(0);
  const started = useRef(false);

  const boot = useCallback(async () => {
    setStage("loading");
    setBootError(null);
    try {
      const status = await authApi.setupStatus();
      setSetupStatus(status);
      if (!status.initialized) {
        setUser(null);
        setStage("setup");
        return;
      }
      const refreshed = await refreshAccessToken();
      if (!refreshed) {
        setUser(null);
        setStage("login");
        return;
      }
      setAccessToken(refreshed.access_token);
      setUser(refreshed.user);
      setStage("authenticated");
    } catch (error) {
      const message =
        error instanceof ApiError
          ? error.message
          : "No fue posible contactar el servicio. Verifique que el backend esté en ejecución.";
      setBootError(message);
      setStage("offline");
    }
  }, []);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    void boot();
  }, [boot, bootAttempt]);

  useEffect(() => {
    setAuthFailureHandler(() => {
      setAccessToken(null);
      setUser(null);
      queryClient.clear();
      setStage("login");
    });
    return () => setAuthFailureHandler(null);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const response = await authApi.login({ email, password });
    queryClient.clear();
    setUser(response.user);
    setStage("authenticated");
  }, []);

  const initialize = useCallback<AuthContextValue["initialize"]>(async (payload) => {
    const response = await authApi.setup(payload);
    queryClient.clear();
    setUser(response.user);
    setSetupStatus({
      initialized: true,
      organization_name: payload.organization_name,
      product_name: "CIS Hardening Auditor",
      version: "1.0.0",
    });
    setStage("authenticated");
  }, []);

  const logout = useCallback(async () => {
    await authApi.logout();
    setAccessToken(null);
    queryClient.clear();
    setUser(null);
    setStage("login");
  }, []);

  const refreshUser = useCallback(async () => {
    const current = await authApi.me();
    setUser(current);
  }, []);

  const hasPermission = useCallback(
    (code: string) => Boolean(user?.permissions.includes(code)),
    [user],
  );

  const hasAnyPermission = useCallback(
    (...codes: string[]) => codes.some((code) => Boolean(user?.permissions.includes(code))),
    [user],
  );

  const retryBoot = useCallback(() => {
    started.current = false;
    setBootAttempt((attempt) => attempt + 1);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        stage,
        user,
        setupStatus,
        bootError,
        login,
        initialize,
        logout,
        retryBoot,
        refreshUser,
        hasPermission,
        hasAnyPermission,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return value;
}
