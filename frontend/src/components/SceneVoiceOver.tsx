import { useEffect, useState } from "react";
import { Loader2, Mic2, Volume2 } from "lucide-react";
import { generateSceneAudio, getSceneAudioBlobUrl, getSceneAudioStatus } from "../services/api/ttsService";

interface Props {
  sceneId: string;
  hasAudio?: boolean;
  onGenerated?: () => void;
}

export function SceneVoiceOver({ sceneId, hasAudio = false, onGenerated }: Props) {
  const [loading, setLoading] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [retryAfter, setRetryAfter] = useState(0);

  useEffect(() => {
    let active = true;
    getSceneAudioStatus(sceneId)
      .then(async (status) => {
        if (!active || !status.has_audio) return;
        const url = await getSceneAudioBlobUrl(sceneId);
        if (active) setAudioUrl(url);
        else URL.revokeObjectURL(url);
      })
      .catch(() => {});
    return () => {
      active = false;
      setAudioUrl((current) => {
        if (current) URL.revokeObjectURL(current);
        return null;
      });
    };
  }, [sceneId, hasAudio]);

  useEffect(() => {
    if (retryAfter <= 0) return;
    const timer = window.setInterval(() => setRetryAfter((value) => Math.max(0, value - 1)), 1000);
    return () => window.clearInterval(timer);
  }, [retryAfter]);

  async function handleGenerate(forceRegenerate = false) {
    setLoading(true);
    setError("");
    try {
      await generateSceneAudio(sceneId, "Kore", forceRegenerate);
      const url = await getSceneAudioBlobUrl(sceneId);
      setAudioUrl((previous) => {
        if (previous) URL.revokeObjectURL(previous);
        return url;
      });
      onGenerated?.();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Voice generation failed.";
      setError(message);
      const match = message.match(/about (\d+) seconds?/i);
      if (match) setRetryAfter(Number(match[1]));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mt-3 rounded-xl border border-slate-200 bg-white p-3">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-700">
          <Mic2 className="h-4 w-4" /> AI voice-over
        </div>
        <button type="button" onClick={() => handleGenerate(false)} disabled={loading || retryAfter > 0}
          className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-3 py-2 text-xs font-medium text-white disabled:opacity-60">
          {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Volume2 className="h-3.5 w-3.5" />}
          {loading ? "Generating..." : retryAfter > 0 ? `Wait ${retryAfter}s` : audioUrl ? "Use cached voice" : "Generate voice"}
        </button>
      </div>
      {audioUrl && <div className="mt-3 space-y-2"><audio className="w-full" controls src={audioUrl} /><button type="button" onClick={() => handleGenerate(true)} disabled={loading || retryAfter > 0} className="text-[11px] font-medium text-slate-500 hover:text-slate-900 disabled:opacity-50">Regenerate with Gemini</button></div>}
      {error && <p className="mt-2 text-xs text-red-600">{error}</p>}
    </div>
  );
}
