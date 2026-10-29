import { NavLink } from "react-router-dom";
import { Clapperboard, FolderKanban, Image, LayoutTemplate, LogOut, Settings, Sparkles, Video } from "lucide-react";
import { useAuth } from "../../context/AuthContext";

const links=[["/","Dashboard",Clapperboard],["/create","Create Video",Sparkles],["/projects","Projects",FolderKanban],["/templates","Templates",LayoutTemplate],["/media","Media",Image],["/settings","Settings",Settings]] as const;

export default function Sidebar(){
 const {user,logout}=useAuth();
 return <aside className="flex w-64 shrink-0 flex-col border-r border-slate-200 bg-white">
  <div className="flex h-16 items-center gap-3 border-b px-5"><div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-900 text-white"><Video className="h-4 w-4"/></div><div><p className="text-sm font-semibold">AI Video Studio</p><p className="text-[10px] text-slate-400">Creative workspace</p></div></div>
  <nav className="flex-1 space-y-1 p-3">{links.map(([to,label,Icon])=><NavLink key={to} to={to} end={to==="/"} className={({isActive})=>`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium ${isActive?"bg-slate-900 text-white":"text-slate-600 hover:bg-slate-50"}`}><Icon className="h-4 w-4"/>{label}</NavLink>)}</nav>
  <div className="border-t p-3"><div className="mb-2 rounded-xl bg-slate-50 p-3"><p className="truncate text-xs font-medium">{user?.full_name||user?.email}</p><p className="truncate text-[11px] text-slate-400">{user?.email}</p></div><button onClick={logout} className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-slate-500 hover:bg-slate-50"><LogOut className="h-4 w-4"/>Sign out</button></div>
 </aside>;
}
