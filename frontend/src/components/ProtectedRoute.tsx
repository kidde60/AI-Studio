import { Navigate, Outlet, useLocation } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute(){
  const {user,loading}=useAuth(); const location=useLocation();
  if(loading) return <div className="flex min-h-screen items-center justify-center"><Loader2 className="h-6 w-6 animate-spin"/></div>;
  if(!user) return <Navigate to="/login" replace state={{from:location.pathname}} />;
  return <Outlet />;
}
