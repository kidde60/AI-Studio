import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { SceneVoiceOver } from "../components/SceneVoiceOver";
import {
  listAssets,
  assetFileUrl,
  type UserAsset,
} from "../services/api/assetService";
import { selectUserAsset } from "../services/api/storyboardService";
import { autoProductionAssets, updateScene } from "../services/api/productionAssetsService";
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  Check,
  Image,
  Loader2,
  Mic2,
  Music2,
  Play,
  Search,
  Sparkles,
  Timer,
  X,
} from "lucide-react";
import type { GeneratedContent } from "../types/content";
import type { Project } from "../services/api/projectService";
import {
  getStoryboard,
  searchSceneMedia,
  selectSceneMedia,
  type MediaResult,
  type Storyboard as StoryboardData,
} from "../services/api/storyboardService";

export default function Storyboard() {
  const { storyboardId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const content = location.state?.content as GeneratedContent | undefined;
  const project = location.state?.project as Project | undefined;
  const initialStoryboard = location.state?.storyboard as
    | StoryboardData
    | undefined;

  const [storyboard, setStoryboard] = useState<StoryboardData | null>(
    initialStoryboard ?? null,
  );
  const [loading, setLoading] = useState(!initialStoryboard);
  const [error, setError] = useState("");
  const [mediaResults, setMediaResults] = useState<
    Record<string, MediaResult[]>
  >({});
  const [mediaQueries, setMediaQueries] = useState<Record<string, string>>({});
  const [searchingScene, setSearchingScene] = useState<string | null>(null);
  const [selectingMedia, setSelectingMedia] = useState<string | null>(null);
  const [mediaError, setMediaError] = useState("");
  const [userAssets, setUserAssets] = useState<UserAsset[]>([]);
  const [assetPickerScene, setAssetPickerScene] = useState<string | null>(null);
  const [autoProducing, setAutoProducing] = useState(false);
  const [autoStatus, setAutoStatus] = useState("");
  const [savingScene, setSavingScene] = useState<string | null>(null);

  useEffect(() => {
    if (!storyboardId || initialStoryboard?.id === storyboardId) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    getStoryboard(storyboardId)
      .then((result) => {
        if (!cancelled) setStoryboard(result);
      })
      .catch((err) => {
        if (!cancelled)
          setError(
            err instanceof Error ? err.message : "Could not load storyboard.",
          );
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [storyboardId, initialStoryboard?.id]);

  useEffect(() => {
    listAssets()
      .then(setUserAssets)
      .catch(() => undefined);
  }, []);

  const totalDuration = useMemo(
    () =>
      storyboard?.scenes.reduce(
        (sum, scene) => sum + scene.duration_seconds,
        0,
      ) ?? 0,
    [storyboard],
  );

  const handleFindMedia = async (sceneId: string) => {
    if (!storyboardId) return;
    setSearchingScene(sceneId);
    setMediaError("");
    try {
      const result = await searchSceneMedia(storyboardId, sceneId);
      setMediaResults((current) => ({ ...current, [sceneId]: result.results }));
      setMediaQueries((current) => ({ ...current, [sceneId]: result.query }));
    } catch (err) {
      setMediaError(
        err instanceof Error ? err.message : "Could not search stock media.",
      );
    } finally {
      setSearchingScene(null);
    }
  };

  const handleUseMedia = async (sceneId: string, media: MediaResult) => {
    if (!storyboardId) return;
    setSelectingMedia(`${sceneId}:${media.id}`);
    setMediaError("");
    try {
      const result = await selectSceneMedia(storyboardId, sceneId, media);
      setStoryboard((current) =>
        current
          ? {
              ...current,
              scenes: current.scenes.map((scene) =>
                scene.id === sceneId ? result.scene : scene,
              ),
            }
          : current,
      );
      setMediaResults((current) => ({ ...current, [sceneId]: [] }));
    } catch (err) {
      setMediaError(
        err instanceof Error
          ? err.message
          : "Could not attach media to this scene.",
      );
    } finally {
      setSelectingMedia(null);
    }
  };

  const handleUseUserAsset = async (sceneId: string, assetId: string) => {
    if (!storyboardId) return;
    setSelectingMedia(`${sceneId}:user:${assetId}`);
    setMediaError("");
    try {
      const result = await selectUserAsset(storyboardId, sceneId, assetId);
      setStoryboard((current) =>
        current
          ? {
              ...current,
              scenes: current.scenes.map((scene) =>
                scene.id === sceneId ? result.scene : scene,
              ),
            }
          : current,
      );
      setAssetPickerScene(null);
    } catch (err) {
      setMediaError(
        err instanceof Error ? err.message : "Could not attach your asset.",
      );
    } finally {
      setSelectingMedia(null);
    }
  };

  const handleFindAll = async () => {
    if (!storyboard) return;
    for (const scene of storyboard.scenes) {
      await handleFindMedia(scene.id);
    }
  };

  const handleAutoProduction = async () => {
    if (!storyboardId) return;
    setAutoProducing(true);
    setMediaError("");
    setAutoStatus("Automatically selecting media and generating voice-over...");
    try {
      const result = await autoProductionAssets(storyboardId);
      const latest = await getStoryboard(storyboardId);
      setStoryboard(latest);
      const mediaCount = result.scenes.filter((item) => item.media_attached || item.skipped_media).length;
      const voiceCount = result.scenes.filter((item) => item.voice_attached || item.skipped_voice).length;
      const errors = result.scenes.filter((item) => item.error).length;
      setAutoStatus(`Production assets processed: ${mediaCount}/${result.scenes.length} media, ${voiceCount}/${result.scenes.length} voice-over${errors ? `, ${errors} scene${errors === 1 ? "" : "s"} need attention` : ""}.`);
    } catch (err) {
      setMediaError(err instanceof Error ? err.message : "Automatic production failed.");
      setAutoStatus("");
    } finally {
      setAutoProducing(false);
    }
  };

  const handleDurationSave = async (sceneId: string, duration: number) => {
    if (!Number.isFinite(duration) || duration <= 0 || duration > 180) return;
    setSavingScene(sceneId);
    setMediaError("");
    try {
      const updated = await updateScene(sceneId, { duration_seconds: duration });
      setStoryboard((current) => current ? { ...current, scenes: current.scenes.map((scene) => scene.id === sceneId ? updated : scene) } : current);
    } catch (err) {
      setMediaError(err instanceof Error ? err.message : "Could not update scene duration.");
    } finally {
      setSavingScene(null);
    }
  };

  if (loading)
    return (
      <div className="mx-auto flex min-h-[55vh] items-center justify-center">
        <div className="text-center">
          <Loader2 className="mx-auto h-7 w-7 animate-spin text-slate-500" />
          <p className="mt-3 text-sm text-slate-500">
            Loading your AI storyboard...
          </p>
        </div>
      </div>
    );

  if (error || !storyboard)
    return (
      <div className="mx-auto max-w-3xl px-6 py-16">
        <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
          <AlertCircle className="mx-auto h-9 w-9 text-slate-400" />
          <h1 className="mt-4 text-xl font-semibold">Storyboard unavailable</h1>
          <p className="mt-2 text-sm text-slate-500">
            {error || "We could not find this storyboard."}
          </p>
          <button
            onClick={() => navigate("/create")}
            className="mt-5 rounded-xl bg-slate-900 px-5 py-3 text-sm font-medium text-white"
          >
            Create a new video
          </button>
        </div>
      </div>
    );

  return (
    <div className="mx-auto max-w-6xl px-6 py-7">
      <div className="mb-7 flex flex-wrap items-end justify-between gap-4">
        <div>
          <button
            onClick={() =>
              content
                ? navigate("/content-results", { state: { content } })
                : navigate("/projects")
            }
            className="mb-3 inline-flex items-center gap-2 text-sm text-slate-500 hover:text-slate-900"
          >
            <ArrowLeft className="h-4 w-4" />
            Back
          </button>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            <Sparkles className="h-4 w-4" />
            AI Storyboard
          </div>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">
            {storyboard.title}
          </h1>
          <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-500">
            {storyboard.description ||
              "Gemini-generated scene plan ready for production."}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={handleAutoProduction}
            disabled={autoProducing}
            className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-3 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-60"
          >
            {autoProducing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            {autoProducing ? "Generating..." : "Auto-generate production"}
          </button>
          <button
            onClick={handleFindAll}
            disabled={searchingScene !== null || autoProducing}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-60"
          >
            <Search className="h-4 w-4" />
            Find media manually
          </button>
          <button
            onClick={() =>
              navigate("/editor", {
                state: {
                  content,
                  project,
                  storyboard,
                  scenes: storyboard.scenes,
                },
              })
            }
            className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-5 py-3 text-sm font-medium text-white hover:bg-slate-800"
          >
            Open Editor
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </div>

      {autoStatus && (
        <div className="mb-5 flex items-start gap-2 rounded-xl border border-slate-200 bg-white p-3 text-sm text-slate-600">
          <Sparkles className="mt-0.5 h-4 w-4 shrink-0" />
          {autoStatus}
        </div>
      )}

      {mediaError && (
        <div className="mb-5 flex items-start gap-2 rounded-xl border border-red-100 bg-red-50 p-3 text-sm text-red-700">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          {mediaError}
        </div>
      )}

      <div className="mb-5 grid gap-3 sm:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
          <p className="text-xs text-slate-400">Scenes</p>
          <p className="mt-1 text-lg font-semibold">
            {storyboard.scenes.length}
          </p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
          <p className="text-xs text-slate-400">Planned duration</p>
          <p className="mt-1 text-lg font-semibold">
            {totalDuration.toFixed(1)}s
          </p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
          <p className="text-xs text-slate-400">Media attached</p>
          <p className="mt-1 text-lg font-semibold">
            {storyboard.scenes.filter((s) => s.media_asset_ids?.length).length}/
            {storyboard.scenes.length}
          </p>
        </div>
      </div>

      <div className="grid gap-5 lg:grid-cols-[1fr_300px]">
        <section className="space-y-4">
          {storyboard.scenes.map((scene) => {
            const selected = scene.media_asset_ids?.[0];
            const selectedFileUrl =
              selected?.source === "user_upload"
                ? assetFileUrl(selected.id)
                : selected?.files?.[0]?.url || selected?.url;
            const results = mediaResults[scene.id] || [];
            return (
              <div
                key={scene.id}
                className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
              >
                <div className="grid gap-4 md:grid-cols-[180px_1fr_auto] md:items-start">
                  <div className="overflow-hidden rounded-xl bg-slate-100">
                    {selected?.type === "video" && selectedFileUrl ? (
                      <video
                        src={selectedFileUrl}
                        poster={selected.thumbnail}
                        controls
                        className="h-32 w-full object-cover"
                      />
                    ) : selected?.type === "image" && selectedFileUrl ? (
                      <img
                        src={selectedFileUrl}
                        alt={selected.description || selected.id || scene.title}
                        className="h-32 w-full object-cover"
                      />
                    ) : (
                      <div className="flex h-32 flex-col items-center justify-center text-slate-400">
                        <Image className="h-7 w-7" />
                        <span className="mt-2 text-[10px] font-medium uppercase tracking-wide">
                          Media pending
                        </span>
                      </div>
                    )}
                  </div>
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs font-semibold text-slate-400">
                        SCENE {String(scene.scene_order).padStart(2, "0")}
                      </span>
                      <label className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-1 text-[10px] text-slate-500">
                        <Timer className="h-3 w-3" />
                        <input
                          aria-label={`Scene ${scene.scene_order} duration in seconds`}
                          type="number"
                          min="0.5"
                          max="180"
                          step="0.5"
                          defaultValue={scene.duration_seconds}
                          onBlur={(event) => {
                            const value = Number(event.target.value);
                            if (value !== scene.duration_seconds) void handleDurationSave(scene.id, value);
                          }}
                          className="w-14 bg-transparent text-[10px] font-medium outline-none"
                        />
                        s
                        {savingScene === scene.id && <Loader2 className="h-3 w-3 animate-spin" />}
                      </label>
                      <span className="rounded-full bg-slate-100 px-2 py-1 text-[10px] capitalize text-slate-500">
                        {scene.transition}
                      </span>
                    </div>
                    <h2 className="mt-2 font-semibold text-slate-900">
                      {scene.title}
                    </h2>
                    <div className="mt-3 grid gap-3 lg:grid-cols-2">
                      <div className="rounded-xl bg-slate-50 p-3">
                        <p className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                          <Mic2 className="h-3 w-3" />
                          Narration
                        </p>
                        <p className="mt-2 text-sm leading-6 text-slate-600">
                          {scene.narration || "No narration for this scene."}
                        </p>
                      </div>
                      <div className="rounded-xl bg-slate-50 p-3">
                        <p className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                          <Image className="h-3 w-3" />
                          Visual direction
                        </p>
                        <p className="mt-2 text-sm leading-6 text-slate-600">
                          {scene.visual_description ||
                            "Visual direction not provided."}
                        </p>
                      </div>
                    </div>
                    <SceneVoiceOver sceneId={scene.id} hasAudio={false} />
                  </div>
                  <div className="flex flex-col gap-2">
                    <button
                      onClick={() =>
                        setAssetPickerScene(
                          assetPickerScene === scene.id ? null : scene.id,
                        )
                      }
                      className="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50"
                    >
                      My assets
                    </button>
                    <button
                      onClick={() => handleFindMedia(scene.id)}
                      disabled={searchingScene === scene.id}
                      className="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-60"
                    >
                      <Search className="h-4 w-4" />
                      {searchingScene === scene.id
                        ? "Searching..."
                        : selected
                          ? "Change media"
                          : "Find media"}
                    </button>
                  </div>
                </div>

                {assetPickerScene === scene.id && (
                  <div className="mt-4 rounded-xl border border-slate-200 bg-white p-3">
                    <p className="mb-3 text-xs font-semibold text-slate-700">
                      Choose one of your uploaded assets
                    </p>
                    {userAssets.length === 0 ? (
                      <p className="text-xs text-slate-500">
                        No uploads yet. Add them from Media Library.
                      </p>
                    ) : (
                      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                        {userAssets
                          .filter((a) => a.asset_type !== "audio")
                          .map((asset) => (
                            <button
                              key={asset.id}
                              onClick={() =>
                                void handleUseUserAsset(scene.id, asset.id)
                              }
                              className="overflow-hidden rounded-xl border border-slate-200 bg-white text-left hover:border-slate-400"
                            >
                              {asset.asset_type === "video" ? (
                                <video
                                  src={assetFileUrl(asset.id)}
                                  className="aspect-video w-full object-cover"
                                  muted
                                />
                              ) : (
                                <img
                                  src={assetFileUrl(asset.id)}
                                  alt={asset.file_name}
                                  className="aspect-video w-full object-cover"
                                />
                              )}
                              <div className="p-2">
                                <p className="truncate text-xs font-medium">
                                  {asset.file_name}
                                </p>
                                <p className="text-[10px] uppercase text-slate-400">
                                  {asset.asset_type}
                                </p>
                              </div>
                            </button>
                          ))}
                      </div>
                    )}
                  </div>
                )}

                {results.length > 0 && (
                  <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-3">
                    <div className="mb-3 flex items-center justify-between">
                      <div>
                        <p className="text-xs font-semibold text-slate-700">
                          Stock matches
                        </p>
                        <p className="text-[11px] text-slate-400">
                          Search: {mediaQueries[scene.id]}
                        </p>
                      </div>
                      <button
                        onClick={() =>
                          setMediaResults((current) => ({
                            ...current,
                            [scene.id]: [],
                          }))
                        }
                        className="p-1 text-slate-400 hover:text-slate-700"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                      {results.map((media) => (
                        <div
                          key={`${media.provider}-${media.id}`}
                          className="overflow-hidden rounded-xl border border-slate-200 bg-white"
                        >
                          <div className="aspect-video bg-slate-100">
                            {media.files?.[0]?.url ? (
                              <video
                                src={media.files[0].url}
                                poster={media.thumbnail}
                                muted
                                className="h-full w-full object-cover"
                              />
                            ) : media.thumbnail ? (
                              <img
                                src={media.thumbnail}
                                alt={media.description || "Stock media"}
                                className="h-full w-full object-cover"
                              />
                            ) : null}
                          </div>
                          <div className="p-3">
                            <p className="text-[10px] font-semibold uppercase text-slate-400">
                              {media.source || media.provider}
                            </p>
                            <button
                              onClick={() => handleUseMedia(scene.id, media)}
                              disabled={
                                selectingMedia === `${scene.id}:${media.id}`
                              }
                              className="mt-2 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-slate-900 px-3 py-2 text-xs font-medium text-white disabled:opacity-60"
                            >
                              {selectingMedia === `${scene.id}:${media.id}` ? (
                                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                              ) : (
                                <Check className="h-3.5 w-3.5" />
                              )}
                              {selectingMedia === `${scene.id}:${media.id}`
                                ? "Attaching..."
                                : "Use this media"}
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </section>

        <aside className="space-y-4">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-3 flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-slate-500" />
              <h2 className="font-semibold text-slate-900">
                Production progress
              </h2>
            </div>
            <div className="space-y-3">
              <div className="flex items-center gap-3 rounded-xl bg-slate-50 p-3">
                <Image className="h-4 w-4 text-slate-500" />
                <div>
                  <p className="text-xs font-medium text-slate-700">
                    Stock media
                  </p>
                  <p className="text-[11px] text-slate-400">
                    {
                      storyboard.scenes.filter((s) => s.media_asset_ids?.length)
                        .length
                    }{" "}
                    of {storyboard.scenes.length} scenes attached
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3 rounded-xl bg-slate-50 p-3">
                <Mic2 className="h-4 w-4 text-slate-500" />
                <div>
                  <p className="text-xs font-medium text-slate-700">AI Voice</p>
                  <p className="text-[11px] text-slate-400">
                    {storyboard.scenes.filter((s) => s.narration).length} scenes with narration — auto-generated above
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3 rounded-xl bg-slate-50 p-3">
                <Music2 className="h-4 w-4 text-slate-500" />
                <div>
                  <p className="text-xs font-medium text-slate-700">
                    Background music
                  </p>
                  <p className="text-[11px] text-slate-400">Not selected yet</p>
                </div>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
