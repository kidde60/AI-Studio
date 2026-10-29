import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { getAccessToken } from "../services/api/client";
import { login as apiLogin, logout as apiLogout, me, register as apiRegister, type User } from "../services/api/authService";

type AuthValue = {
  user: User | null; loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
};
const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({children}:{children:ReactNode}) {
  const [user,setUser]=useState<User|null>(null);
  const [loading,setLoading]=useState(true);
  useEffect(()=>{ if(!getAccessToken()){setLoading(false);return;} me().then(setUser).catch(apiLogout).finally(()=>setLoading(false)); },[]);
  return <AuthContext.Provider value={{
    user,loading,
    async login(e,p){setUser(await apiLogin(e,p));},
    async register(e,p,n){setUser(await apiRegister(e,p,n));},
    logout(){apiLogout();setUser(null);}
  }}>{children}</AuthContext.Provider>;
}
export function useAuth(){const c=useContext(AuthContext); if(!c) throw new Error("useAuth must be inside AuthProvider"); return c;}
