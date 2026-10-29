import { FormEvent, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Loader2, Sparkles } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Auth({mode}:{mode:"login"|"register"}){
  const {login,register}=useAuth(); const navigate=useNavigate(); const location=useLocation();
  const [email,setEmail]=useState(""); const [password,setPassword]=useState(""); const [name,setName]=useState("");
  const [error,setError]=useState(""); const [busy,setBusy]=useState(false); const isRegister=mode==="register";
  async function submit(e:FormEvent){e.preventDefault();setBusy(true);setError("");try{
    if(isRegister) await register(email,password,name); else await login(email,password);
    navigate((location.state as {from?:string}|null)?.from || "/", {replace:true});
  }catch(err){setError(err instanceof Error?err.message:"Authentication failed.");}finally{setBusy(false);}}
  return <div className="flex min-h-screen items-center justify-center bg-slate-50 px-5">
    <form onSubmit={submit} className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-7 shadow-sm">
      <div className="mb-7 text-center"><div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-900 text-white"><Sparkles/></div>
      <h1 className="text-2xl font-semibold">{isRegister?"Create your account":"Welcome back"}</h1>
      <p className="mt-2 text-sm text-slate-500">{isRegister?"Start creating AI-powered videos.":"Sign in to continue."}</p></div>
      {isRegister&&<input value={name} onChange={e=>setName(e.target.value)} placeholder="Full name" className="mb-4 w-full rounded-xl border p-3 text-sm"/>}
      <input required type="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder="Email" className="mb-4 w-full rounded-xl border p-3 text-sm"/>
      <input required minLength={8} type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="Password (8+ characters)" className="w-full rounded-xl border p-3 text-sm"/>
      {error&&<div className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</div>}
      <button disabled={busy} className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-slate-900 p-3 text-sm font-semibold text-white disabled:opacity-60">{busy&&<Loader2 className="h-4 w-4 animate-spin"/>}{isRegister?"Create account":"Sign in"}</button>
      <p className="mt-5 text-center text-sm text-slate-500">{isRegister?"Already have an account?":"Don't have an account?"} <Link className="font-semibold text-slate-900" to={isRegister?"/login":"/register"}>{isRegister?"Sign in":"Create one"}</Link></p>
    </form>
  </div>;
}
