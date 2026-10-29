import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  AlertCircle, Check, ChevronLeft, Download, FileMusic, Loader2,
  Music2, Play, Save, Sparkles, Subtitles, Upload, Video, Volume2,
  WandSparkles, Clock3, Mic2, Image as ImageIcon,
} from "lucide-react";
import { SceneVoiceOver } from "../../components/SceneVoiceOver";
import { assetFileUrl } from "../../services/api/assetService";
import {
  autoProductionAssets, getProductionReadiness, updateScene,
  type ProductionReadiness,
} from "../../services/api/productionAssetsService";
import { getStoryboard, type Storyboard, type StoryboardScene } from "../../services/api/storyboardService";
import {
  createRender, generateSceneSubtitles, getProjectMusic, getRenderJob,
  getRenderVideoUrl, updateProjectMusic, uploadProjectMusic,
  type ProjectMusic, type RenderJob,
} from "../../services/api/productionService";

const PRESETS = {
  shorts: { label: "TikTok / Reels / Shorts", width: 1080, height: 1920 },
  portrait: { label: "Facebook Portrait", width: 1080, height: 1350 },
  square: { label: "Square", width: 1080, height: 1080 },
  landscape: { label: "Landscape", width: 1920, height: 1080 },
} as const;

type PresetKey = keyof typeof PRESETS;

export function Editor() {
  const location = useLocation();
  const navigate = useNavigate();
  const state = location.state as { storyboard?: Storyboard; project?: { id: string; name?: string } } | null;
  const [storyboard, setStoryboard] = useState<Storyboard | null>(state?.storyboard ?? null);
  const [selectedScene, setSelectedScene] = useState(0);
  const [music, setMusic] = useState<ProjectMusic | null>(null);
  const [readiness, setReadiness] = useState<ProductionReadiness | null>(null);
  const [autoLoading, setAutoLoading] = useState(false);
  const [subtitleLoading, setSubtitleLoading] = useState(false);
  const [musicLoading, setMusicLoading] = useState(false);
  const [renderLoading, setRenderLoading] = useState(false);
  const [renderJob, setRenderJob] = useState<RenderJob | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [volume, setVolume] = useState(0.15);
  const [fadeIn, setFadeIn] = useState(1);
  const [fadeOut, setFadeOut] = useState(1);
  const [preset, setPreset] = useState<PresetKey>("shorts");
  const [saving, setSaving] = useState(false);
  const [draft, setDraft] = useState({ title: "", narration: "", duration: 5, transition: "cut" });

  const projectId = state?.project?.id || storyboard?.project_id;
  const scenes = storyboard?.scenes ?? [];
  const scene = scenes[selectedScene];
  const totalDuration = useMemo(() => scenes.reduce((sum, item) => sum + item.duration_seconds, 0), [scenes]);

  useEffect(() => {
    if (storyboard || !location.search) return;
    const id = new URLSearchParams(location.search).get("storyboardId");
    if (id) getStoryboard(id).then(setStoryboard).catch((err) => setError(err instanceof Error ? err.message : "Could not load storyboard."));
  }, [location.search, storyboard]);

  useEffect(() => {
    if (!scene) return;
    setDraft({ title: scene.title, narration: scene.narration || "", duration: scene.duration_seconds, transition: scene.transition || "cut" });
  }, [scene?.id, scene?.title, scene?.narration, scene?.duration_seconds, scene?.transition]);

  const refreshProduction = async () => {
    if (!storyboard?.id) return;
    const [status, musicData] = await Promise.all([
      getProductionReadiness(storyboard.id).catch(() => null),
      projectId ? getProjectMusic(projectId).catch(() => null) : Promise.resolve(null),
    ]);
    if (status) setReadiness(status);
    if (musicData) {
      setMusic(musicData);
      if (musicData.volume != null) setVolume(musicData.volume);
      if (musicData.fade_in_seconds != null) setFadeIn(musicData.fade_in_seconds);
      if (musicData.fade_out_seconds != null) setFadeOut(musicData.fade_out_seconds);
    }
  };

  useEffect(() => { void refreshProduction(); }, [storyboard?.id, projectId, scenes.length]);

  const updateLocalScene = (updated: StoryboardScene) => {
    setStoryboard((current) => current ? { ...current, scenes: current.scenes.map((item) => item.id === updated.id ? updated : item) } : current);
  };

  const saveScene = async () => {
    if (!scene) return;
    setSaving(true); setError(""); setNotice("");
    try {
      const updated = await updateScene(scene.id, {
        title: draft.title.trim() || scene.title,
        narration: draft.narration,
        duration_seconds: draft.duration,
        transition: draft.transition,
      });
      updateLocalScene(updated);
      await refreshProduction();
      setNotice("Scene changes saved.");
    } catch (err) { setError(err instanceof Error ? err.message : "Could not save scene."); }
    finally { setSaving(false); }
  };

  const handleAutoProduction = async () => {
    if (!storyboard) return;
    setAutoLoading(true); setError(""); setNotice("");
    try {
      const result = await autoProductionAssets(storyboard.id);
      const latest = await getStoryboard(storyboard.id);
      setStoryboard(latest);
      await refreshProduction();
      const failed = result.scenes.filter((item) => item.error).length;
      setNotice(failed ? `Production completed with ${failed} scene${failed === 1 ? "" : "s"} needing attention.` : "Media, voice-over and subtitles are ready for review.");
    } catch (err) { setError(err instanceof Error ? err.message : "Automatic production failed."); }
    finally { setAutoLoading(false); }
  };

  const handleGenerateSubtitles = async () => {
    if (!scenes.length) return;
    setSubtitleLoading(true); setError("");
    try {
      await Promise.all(scenes.map((item) => item.narration ? generateSceneSubtitles(item.id, true) : Promise.resolve()));
      await refreshProduction();
      setNotice("Subtitles generated for all narrated scenes.");
    } catch (err) { setError(err instanceof Error ? err.message : "Could not generate subtitles."); }
    finally { setSubtitleLoading(false); }
  };

  const handleMusic = async (file: File) => {
    if (!projectId) return;
    setMusicLoading(true); setError("");
    try {
      const result = await uploadProjectMusic(projectId, file);
      setMusic(result);
      setNotice("Background music uploaded.");
    } catch (err) { setError(err instanceof Error ? err.message : "Could not upload music."); }
    finally { setMusicLoading(false); }
  };

  const saveMusic = async () => {
    if (!projectId || !music?.has_music) return;
    setMusicLoading(true); setError("");
    try {
      const result = await updateProjectMusic(projectId, { volume, fade_in_seconds: fadeIn, fade_out_seconds: fadeOut });
      setMusic(result);
      setNotice("Music settings saved.");
    } catch (err) { setError(err instanceof Error ? err.message : "Could not save music settings."); }
    finally { setMusicLoading(false); }
  };

  const handleRender = async () => {
    if (!projectId || !storyboard) return;
    if (readiness && readiness.ready_scenes < readiness.total_scenes) {
      setError("Complete the missing production assets before rendering. Use Auto-generate production or fix the flagged scenes.");
      return;
    }
    setRenderLoading(true); setError(""); setNotice(""); setVideoUrl(null); setRenderJob(null);
    try {
      const selected = PRESETS[preset];
      const job = await createRender(projectId, storyboard.id, selected.width, selected.height);
      setRenderJob(job);
      let current = job;
      for (let i = 0; i < 180 && (current.status === "queued" || current.status === "rendering"); i++) {
        await new Promise((resolve) => setTimeout(resolve, 1500));
        current = await getRenderJob(job.id);
        setRenderJob(current);
      }
      if (current.status === "completed") {
        setVideoUrl(await getRenderVideoUrl(current.id));
        setNotice("Your final video is ready.");
      } else if (current.status === "failed") {
        setError(current.error_message || "Video rendering failed.");
      }
    } catch (err) { setError(err instanceof Error ? err.message : "Could not start video rendering."); }
    finally { setRenderLoading(false); }
  };

  if (!storyboard) return <div className="panel p-8 text-center"><AlertCircle className="mx-auto"/><p className="mt-3 text-sm text-muted">Open the editor from a storyboard so the production pipeline can load the project.</p><button className="btn-primary mt-4" onClick={() => navigate("/projects")}>Go to projects</button></div>;

  const readyPercent = readiness?.total_scenes ? Math.round((readiness.ready_scenes / readiness.total_scenes) * 100) : 0;
  const media = scene?.media_asset_ids?.[0];
  const mediaPreview = media?.source === "user_upload" && media?.id ? assetFileUrl(media.id) : media?.files?.[0]?.url || media?.url || media?.thumbnail;

  return <div className="space-y-5">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <button onClick={() => navigate(`/storyboard/${storyboard.id}`, { state: { storyboard } })} className="flex items-center gap-1 text-sm font-medium text-muted"><ChevronLeft size={17}/>Storyboard</button>
      <div className="flex flex-wrap gap-2">
        <button onClick={handleAutoProduction} disabled={autoLoading} className="btn-secondary"><WandSparkles size={16}/>{autoLoading ? "Generating..." : "Auto-generate production"}</button>
        <button onClick={handleRender} disabled={renderLoading || readyPercent < 100} className="btn-primary">{renderLoading ? <Loader2 size={16} className="animate-spin"/> : <Download size={16}/>} {renderLoading ? "Rendering..." : "Render MP4"}</button>
      </div>
    </div>

    {error && <div className="flex items-start gap-2 rounded-xl border border-red-100 bg-red-50 p-3 text-sm text-red-700"><AlertCircle size={17} className="mt-0.5 shrink-0"/>{error}</div>}
    {notice && <div className="flex items-center gap-2 rounded-xl border border-emerald-100 bg-emerald-50 p-3 text-sm text-emerald-700"><Check size={17}/>{notice}</div>}

    <div className="grid gap-5 xl:grid-cols-[1fr_360px]">
      <div className="space-y-5">
        <div className="panel overflow-hidden bg-neutral-950">
          <div className="flex min-h-[600px] items-center justify-center p-6">
            {videoUrl ? <video src={videoUrl} controls autoPlay className="max-h-[70vh] rounded-2xl bg-black"/> : <div className="relative aspect-[9/16] h-[540px] max-w-full overflow-hidden rounded-2xl bg-neutral-800">
              {media?.type === "video" && mediaPreview ? <video src={mediaPreview} muted loop autoPlay className="h-full w-full object-cover"/> : mediaPreview ? <img src={mediaPreview} className="h-full w-full object-cover"/> : <div className="absolute inset-0 flex items-center justify-center text-neutral-500"><Play size={34}/></div>}
              {scene?.narration && <div className="absolute bottom-5 left-4 right-4 rounded-lg bg-black/70 px-4 py-3 text-center text-sm font-semibold text-white">{scene.narration}</div>}
            </div>}
          </div>
        </div>

        {videoUrl && renderJob && <div className="panel flex flex-wrap items-center justify-between gap-3 p-4"><div className="flex items-center gap-3"><Video size={19}/><div><p className="text-sm font-semibold">Final video ready</p><p className="text-xs text-muted">{PRESETS[preset].label} · {PRESETS[preset].width}×{PRESETS[preset].height}</p></div></div><a href={videoUrl} download={`ai-video-${renderJob.id}.mp4`} className="btn-primary"><Download size={15}/>Download video</a></div>}

        <div className="panel p-5">
          <div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="font-semibold">Scenes</h2><p className="mt-1 text-xs text-muted">Edit duration and narration without rebuilding the whole project.</p></div><span className="text-sm text-muted">{Math.round(totalDuration)}s total</span></div>
          <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {scenes.map((item, index) => <button key={item.id} onClick={() => setSelectedScene(index)} className={`rounded-xl border p-3 text-left ${index === selectedScene ? "border-ink bg-neutral-50" : "border-line"}`}><div className="flex items-center justify-between gap-2"><span className="text-xs font-semibold">Scene {item.scene_order}</span><span className="text-[10px] text-muted">{item.duration_seconds}s</span></div><p className="mt-1 truncate text-sm font-medium">{item.title}</p><div className="mt-2 flex gap-2 text-[10px] text-muted"><span>{item.media_asset_ids?.length ? "Media ✓" : "Media —"}</span><span>{item.narration ? "Voice" : "No voice"}</span></div></button>)}
          </div>
        </div>

        {scene && <div className="panel p-5">
          <div className="flex flex-wrap items-center justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-wider text-muted">Scene {scene.scene_order}</p><h2 className="mt-1 text-lg font-semibold">Edit scene</h2></div><button className="btn-primary" onClick={saveScene} disabled={saving}>{saving ? <Loader2 size={15} className="animate-spin"/> : <Save size={15}/>}Save changes</button></div>
          <div className="mt-5 grid gap-4 md:grid-cols-2">
            <label className="block"><span className="text-xs font-semibold">Scene title</span><input className="input mt-2 w-full" value={draft.title} onChange={(e) => setDraft((d) => ({...d, title: e.target.value}))}/></label>
            <label className="block"><span className="text-xs font-semibold">Duration (seconds)</span><div className="mt-2 flex items-center gap-2"><Clock3 size={16}/><input type="number" min="0.5" max="180" step="0.5" className="input w-full" value={draft.duration} onChange={(e) => setDraft((d) => ({...d, duration: Number(e.target.value)}))}/></div></label>
          </div>
          <label className="mt-4 block"><span className="text-xs font-semibold">Narration</span><textarea className="input mt-2 min-h-28 w-full" value={draft.narration} onChange={(e) => setDraft((d) => ({...d, narration: e.target.value}))}/></label>
          <SceneVoiceOver sceneId={scene.id} hasAudio={false}/>
        </div>}
      </div>

      <aside className="space-y-4">
        <div className="panel p-5">
          <div className="flex items-center justify-between"><div><h2 className="font-semibold">Production status</h2><p className="mt-1 text-xs text-muted">Everything should be ready before rendering.</p></div><span className="text-lg font-semibold">{readyPercent}%</span></div>
          <div className="mt-3 h-2 rounded-full bg-neutral-100"><div className="h-full rounded-full bg-ink transition-all" style={{width: `${readyPercent}%`}}/></div>
          <div className="mt-5 space-y-2 text-sm">
            {[
              [ImageIcon, "Media", readiness ? `${readiness.media_ready}/${readiness.total_scenes}` : "Checking..."],
              [Mic2, "Voice-over", readiness ? `${readiness.voice_ready}/${readiness.total_scenes}` : "Checking..."],
              [Subtitles, "Subtitles", readiness ? `${readiness.subtitles_ready}/${readiness.total_scenes}` : "Checking..."],
            ].map(([Icon, label, value]) => <div key={String(label)} className="flex items-center justify-between rounded-xl bg-neutral-50 p-3"><span className="flex items-center gap-2"><Icon size={16}/>{String(label)}</span><span className="text-xs font-medium text-muted">{String(value)}</span></div>)}
          </div>
          <button onClick={handleAutoProduction} disabled={autoLoading} className="btn-secondary mt-4 w-full"><Sparkles size={15}/>{autoLoading ? "Generating..." : "Complete automatically"}</button>
          <button onClick={handleGenerateSubtitles} disabled={subtitleLoading} className="btn-secondary mt-2 w-full"><Subtitles size={15}/>{subtitleLoading ? "Generating subtitles..." : "Regenerate all subtitles"}</button>
        </div>

        <div className="panel p-5">
          <div className="flex items-center gap-2"><Music2 size={18}/><div><h2 className="font-semibold">Background music</h2><p className="mt-1 text-xs text-muted">Optional project-level soundtrack.</p></div></div>
          <label className="mt-4 flex cursor-pointer items-center justify-center gap-2 rounded-xl border border-dashed border-line p-4 text-sm font-medium"><Upload size={16}/>{musicLoading ? "Uploading..." : music?.file_name || "Upload music"}<input type="file" accept="audio/*" className="hidden" disabled={musicLoading} onChange={(e) => e.target.files?.[0] && void handleMusic(e.target.files[0])}/></label>
          {music?.has_music && <div className="mt-4 space-y-4"><div><div className="flex justify-between text-xs"><span>Volume</span><span>{Math.round(volume * 100)}%</span></div><input type="range" min="0" max="1" step="0.01" value={volume} onChange={(e) => setVolume(Number(e.target.value))} className="mt-2 w-full"/></div><div className="grid grid-cols-2 gap-3"><label className="text-xs">Fade in<input type="number" min="0" max="30" step="0.5" className="input mt-1 w-full" value={fadeIn} onChange={(e) => setFadeIn(Number(e.target.value))}/></label><label className="text-xs">Fade out<input type="number" min="0" max="30" step="0.5" className="input mt-1 w-full" value={fadeOut} onChange={(e) => setFadeOut(Number(e.target.value))}/></label></div><button className="btn-secondary w-full" onClick={saveMusic} disabled={musicLoading}><Volume2 size={15}/>Save music settings</button></div>}
        </div>

        <div className="panel p-5">
          <div className="flex items-center gap-2"><Video size={18}/><div><h2 className="font-semibold">Export</h2><p className="mt-1 text-xs text-muted">Choose the final video format.</p></div></div>
          <select className="input mt-4 w-full" value={preset} onChange={(e) => setPreset(e.target.value as PresetKey)}>{Object.entries(PRESETS).map(([key, value]) => <option key={key} value={key}>{value.label} — {value.width}×{value.height}</option>)}</select>
          <button onClick={handleRender} disabled={renderLoading || readyPercent < 100} className="btn-primary mt-3 w-full">{renderLoading ? <Loader2 size={16} className="animate-spin"/> : <Download size={16}/>} {renderLoading ? "Rendering..." : "Render final video"}</button>
        </div>
      </aside>
    </div>
  </div>;
}
