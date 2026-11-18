import { useEffect, useState } from "react";
import { AuthContext } from "../../hooks/useAuth";
import { frappeAuth } from "../../services/auth";

const checking = { status: "loading", session: null };

export default function AuthProvider({ children, adapter = frappeAuth }) {
  const [auth, setAuth] = useState(checking);
  const [sessionCheck, setSessionCheck] = useState(0);

  function refreshSession() {
    setAuth(checking);
    setSessionCheck((attempt) => attempt + 1);
  }

  useEffect(() => {
    const controller = new AbortController();

    async function checkSession() {
      try {
        const session = await adapter.getSession(controller.signal);
        if (!controller.signal.aborted) {
          setAuth({ status: session ? "authenticated" : "guest", session });
        }
      } catch {
        if (!controller.signal.aborted) {
          setAuth({ status: "error", session: null });
        }
      }
    }

    checkSession();
    return () => controller.abort();
  }, [adapter, sessionCheck]);

  async function login(username, password) {
    await adapter.login(username, password);
    refreshSession();
  }

  async function logout() {
    await adapter.logout();
    refreshSession();
  }

  return (
    <AuthContext.Provider value={{
      ...auth,
      login,
      logout: adapter.logout ? logout : undefined,
      refreshSession,
      hasPermission: (permission) => auth.session?.permissions?.includes(permission) === true,
    }}>
      {children}
    </AuthContext.Provider>
  );
}
