
import { FormEvent, useEffect, useState } from "react";
import { Image, LoaderCircle, Search, Trash2, Upload, Video, Music2 } from "lucide-react";
import { searchMedia, type MediaResult } from "../../services/api/mediaService";
import { assetFileUrl, deleteAsset, listAssets, uploadAsset, type UserAsset } from "../../services/api/assetService";

export default function Media() {
  const [query, setQuery] = useState("");
  const [type, setType] = useState<"video" | "image">("video");
  const [results, setResults] = useState<MediaResult[]>([]);
  const [assets, setAssets] = useState<UserAsset[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  const refreshAssets = () => listAssets().then(setAssets).catch((err) => setError(err instanceof Error ? err.message : "Could not load your assets."));
  useEffect(() => { void refreshAssets(); }, []);

  async function handleSearch(event: FormEvent) {
    event.preventDefault();
    if (query.trim().length < 2) return;
    setLoading(true); setError("");
    try { setResults((await searchMedia(query.trim(), type)).results); }
    catch (err) { setError(err instanceof Error ? err.message : "Media search failed."); setResults([]); }
    finally { setLoading(false); }
  }

  async function handleUpload(file: File) {
    setUploading(true); setError("");
    try { await uploadAsset(file); await refreshAssets(); }
    catch (err) { setError(err instanceof Error ? err.message : "Upload failed."); }
    finally { setUploading(false); }
  }

  async function remove(id: string) {
    if (!window.confirm("Delete this uploaded asset?")) return;
    try { await deleteAsset(id); await refreshAssets(); }
    catch (err) { setError(err instanceof Error ? err.message : "Could not delete asset."); }
  }

  return <div className="mx-auto max-w-6xl space-y-8">
    <div className="flex flex-wrap items-end justify-between gap-4"><div><h1 className="text-3xl font-bold tracking-tight">Media Library</h1><p className="mt-2 text-sm text-muted">Manage your own assets and search stock media.</p></div><label className="btn-primary cursor-pointer"><Upload size={17}/>{uploading ? "Uploading..." : "Upload asset"}<input type="file" accept="image/*,video/*,audio/*" className="hidden" disabled={uploading} onChange={(e)=>{const f=e.target.files?.[0]; if(f) void handleUpload(f);}}/></label></div>

    {error && <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}

    <section className="panel p-5"><div className="mb-4 flex items-center justify-between"><h2 className="font-semibold">My Assets</h2><span className="text-xs text-muted">{assets.length} uploaded</span></div>{assets.length===0?<p className="text-sm text-muted">Upload images, videos or music here. They can later be assigned to specific scenes.</p>:<div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{assets.map((asset)=><article key={asset.id} className="overflow-hidden rounded-xl border border-line bg-white">{asset.asset_type==="video"?<video src={assetFileUrl(asset.id)} controls className="aspect-video w-full object-cover"/>:asset.asset_type==="image"?<img src={assetFileUrl(asset.id)} alt={asset.file_name} className="aspect-video w-full object-cover"/>:<div className="flex aspect-video items-center justify-center bg-neutral-50"><Music2 size={30}/></div>}<div className="p-3"><p className="truncate text-sm font-medium">{asset.file_name}</p><div className="mt-2 flex items-center justify-between"><span className="text-[10px] uppercase text-muted">{asset.asset_type}</span><button onClick={()=>void remove(asset.id)} className="text-red-500"><Trash2 size={14}/></button></div></div></article>)}</div>}</section>

    <form onSubmit={handleSearch} className="panel flex flex-col gap-3 p-4 md:flex-row"><div className="relative flex-1"><Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" size={18}/><input value={query} onChange={(e)=>setQuery(e.target.value)} className="input pl-10" placeholder="Search stock media"/></div><select value={type} onChange={(e)=>setType(e.target.value as "video"|"image")} className="input md:w-40"><option value="video">Videos</option><option value="image">Images</option></select><button className="btn-primary" disabled={loading}>{loading?<LoaderCircle size={17} className="animate-spin"/>:<Search size={17}/>}Search</button></form>

    {results.length>0&&<div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">{results.map(item=><article key={`${item.provider}-${item.id}`} className="overflow-hidden rounded-2xl border border-line bg-white"><div className="aspect-video bg-neutral-100">{item.type==="video"&&item.files?.[0]?.url?<video src={item.files[0].url} poster={item.thumbnail} controls className="h-full w-full object-cover"/>:item.thumbnail?<img src={item.thumbnail} alt={item.description||"Stock media"} className="h-full w-full object-cover"/>:<div className="flex h-full items-center justify-center text-muted">{item.type==="video"?<Video/>:<Image/>}</div>}</div><div className="p-4"><div className="text-xs font-semibold text-muted">{item.source}</div><p className="mt-1 line-clamp-2 text-sm">{item.description||"Stock media result"}</p></div></article>)}</div>}
  </div>;
}
