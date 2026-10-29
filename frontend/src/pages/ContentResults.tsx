
import { useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ArrowLeft, Check, Copy, AlertCircle, Lightbulb, Loader2, Play, Save, Sparkles } from "lucide-react";
import type { GeneratedContent } from "../types/content";
import { createProject } from "../services/api/projectService";
import { generateStoryboard } from "../services/api/storyboardService";
import { updateContent } from "../services/api/contentService";

export default function ContentResults() {
  const location = useLocation();
  const navigate = useNavigate();
  const initial = location.state?.content as GeneratedContent | undefined;
  const [content, setContent] = useState<GeneratedContent | undefined>(initial);
  const [draft, setDraft] = useState<GeneratedContent | undefined>(initial);
  const [saving, setSaving] = useState(false);
  const [storyboardStatus, setStoryboardStatus] = useState<"idle" | "generating" | "error">("idle");
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);

  const scriptParagraphs = useMemo(() => draft?.script.split("\n\n").filter(Boolean) ?? [], [draft]);

  if (!draft || !content) {
    return <div className="mx-auto max-w-3xl px-6 py-16"><div className="rounded-2xl border border-slate-200 bg-white p-10 text-center shadow-sm"><Sparkles className="mx-auto mb-4 h-10 w-10 text-slate-400"/><h1 className="text-xl font-semibold">No generated content yet</h1><button onClick={() => navigate("/create")} className="mt-6 rounded-xl bg-slate-900 px-5 py-3 text-sm font-medium text-white">Create video</button></div></div>;
  }

  const setField = <K extends keyof GeneratedContent>(key: K, value: GeneratedContent[K]) => {
    setDraft((current) => current ? { ...current, [key]: value } : current);
    setSaved(false);
  };

  const save = async () => {
    if (!draft) return;
    setSaving(true); setError("");
    try {
      const updated = await updateContent(draft.id, {
        title: draft.title,
        hook: draft.hook,
        script: draft.script,
        caption: draft.caption,
        hashtags: draft.hashtags,
        cta: draft.cta,
        content_ideas: draft.contentIdeas,
      });
      setContent(updated);
      setDraft(updated);
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save your content.");
    } finally {
      setSaving(false);
    }
  };

  const continueToStoryboard = async () => {
    if (!draft) return;
    setStoryboardStatus("generating"); setError("");
    try {
      if (!saved) await save();
      const project = await createProject({ name: draft.title, description: `AI video project for: ${draft.topic}`, platform: draft.platform, duration: draft.duration });
      const storyboard = await generateStoryboard(project.id, draft.id);
      navigate(`/storyboard/${storyboard.id}`, { state: { content: draft, project, storyboard } });
    } catch (err) {
      setStoryboardStatus("error");
      setError(err instanceof Error ? err.message : "Could not generate the storyboard.");
    } finally {
      setStoryboardStatus("idle");
    }
  };

  const copy = async (text: string) => { await navigator.clipboard.writeText(text); };

  return <div className="mx-auto max-w-6xl px-6 py-7">
    <div className="mb-7 flex flex-wrap items-end justify-between gap-4">
      <div><button onClick={() => navigate("/create")} className="mb-3 inline-flex items-center gap-2 text-sm text-slate-500 hover:text-slate-900"><ArrowLeft className="h-4 w-4"/>Back to creator</button><div className="flex items-center gap-3"><div className="flex h-11 w-11 items-center justify-center rounded-xl bg-slate-900 text-white"><Sparkles className="h-5 w-5"/></div><div><h1 className="text-2xl font-semibold">AI Content Results</h1><p className="text-sm text-slate-500">Edit the AI draft before it creates scenes and voice-overs.</p></div></div></div>
      <div className="flex gap-2"><button onClick={save} disabled={saving} className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-700 disabled:opacity-60"><Save className="h-4 w-4"/>{saving ? "Saving..." : saved ? "Saved" : "Save changes"}</button><button onClick={continueToStoryboard} disabled={storyboardStatus === "generating"} className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-5 py-3 text-sm font-medium text-white disabled:opacity-60">{storyboardStatus === "generating" ? <Loader2 className="h-4 w-4 animate-spin"/> : <Play className="h-4 w-4"/>}{storyboardStatus === "generating" ? "Generating..." : "Create storyboard"}</button></div>
    </div>

    {error && <div className="mb-5 flex items-start gap-2 rounded-xl border border-red-100 bg-red-50 p-3 text-sm text-red-700"><AlertCircle className="h-4 w-4 mt-0.5"/>{error}</div>}

    <div className="grid gap-5 lg:grid-cols-[1.5fr_0.8fr]">
      <div className="space-y-5">
        {[
          ["title", "Title", "text"],
          ["hook", "Hook", "textarea"],
          ["script", "Script", "textarea"],
          ["caption", "Caption", "textarea"],
          ["cta", "Call to action", "textarea"],
        ].map(([key, label, type]) => (
          <section key={key} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">{label}</label>
            {type === "text" ? <input value={String(draft[key as keyof GeneratedContent])} onChange={(e) => setField(key as keyof GeneratedContent, e.target.value as never)} className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 text-base font-semibold outline-none focus:border-slate-400"/> : <textarea value={String(draft[key as keyof GeneratedContent])} onChange={(e) => setField(key as keyof GeneratedContent, e.target.value as never)} rows={key === "script" ? 12 : 5} className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 text-sm leading-6 outline-none focus:border-slate-400"/>}
          </section>
        ))}
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex items-center justify-between"><label className="text-xs font-semibold uppercase tracking-wider text-slate-400">Hashtags</label><button onClick={() => copy(draft.hashtags.join(" "))} className="text-xs text-slate-500"><Copy className="inline h-3.5 w-3.5 mr-1"/>Copy</button></div><input value={draft.hashtags.join(" ")} onChange={(e) => setField("hashtags", e.target.value.split(/\s+/).filter(Boolean))} className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 text-sm"/></section>
      </div>

      <aside className="space-y-5">
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><h2 className="font-semibold">Content setup</h2><div className="mt-4 space-y-3">{[["Style",draft.style],["Platform",draft.platform],["Duration",`${draft.duration} seconds`],["Audience",draft.targetAudience]].map(([label,value]) => <div key={label} className="flex justify-between gap-3 border-b border-slate-100 pb-3 last:border-0"><span className="text-xs text-slate-400">{label}</span><span className="text-right text-sm font-medium">{value}</span></div>)}</div></section>
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-center gap-2"><Lightbulb className="h-5 w-5 text-slate-500"/><h2 className="font-semibold">More content ideas</h2></div><div className="mt-4 space-y-2">{draft.contentIdeas.map((idea,index)=><button key={idea} onClick={()=>navigate("/create",{state:{topic:idea}})} className="flex w-full items-start gap-3 rounded-xl border border-slate-100 p-3 text-left hover:bg-slate-50"><span className="text-xs font-semibold text-slate-400">0{index+1}</span><span className="text-sm">{idea}</span></button>)}</div></section>
      </aside>
    </div>
  </div>;
}
