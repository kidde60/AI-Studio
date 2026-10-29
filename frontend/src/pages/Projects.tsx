import { useEffect, useState } from "react";
import { FolderKanban, Loader2, Plus, Video } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { listProjects, type Project } from "../services/api/projectService";

export default function Projects(){
 const navigate=useNavigate(); const [projects,setProjects]=useState<Project[]>([]); const [loading,setLoading]=useState(true); const [error,setError]=useState("");
 useEffect(()=>{listProjects().then(setProjects).catch(e=>setError(e instanceof Error?e.message:"Could not load projects.")).finally(()=>setLoading(false));},[]);
 return <div className="mx-auto max-w-6xl px-6 py-7"><div className="mb-7 flex items-center justify-between"><div><h1 className="text-2xl font-semibold">Projects</h1><p className="mt-1 text-sm text-slate-500">Your saved video projects.</p></div><button onClick={()=>navigate("/create")} className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white"><Plus className="h-4 w-4"/>New project</button></div>
 {loading?<div className="flex justify-center py-16"><Loader2 className="animate-spin"/></div>:error?<div className="rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</div>:projects.length===0?<div className="rounded-2xl border border-dashed p-12 text-center"><FolderKanban className="mx-auto text-slate-400"/><h2 className="mt-4 font-semibold">No projects yet</h2><p className="mt-1 text-sm text-slate-500">Generate content and save it as a project.</p></div>:<div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">{projects.map(p=><div key={p.id} className="rounded-2xl border bg-white p-5 shadow-sm"><div className="flex h-32 items-center justify-center rounded-xl bg-slate-100"><Video className="text-slate-400"/></div><h2 className="mt-4 font-semibold">{p.name}</h2><p className="mt-1 text-xs text-slate-500">{p.description||"No description"}</p><div className="mt-4 flex justify-between text-[11px] text-slate-400"><span>{p.platform}</span><span>{p.duration}s</span><span>{p.status}</span></div></div>)}</div>}
 </div>;
}
