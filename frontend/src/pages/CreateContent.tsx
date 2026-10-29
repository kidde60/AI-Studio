import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  ArrowRight,
  Check,
  Clock3,
  FileText,
  Loader2,
  Sparkles,
  Target,
  Users,
  WandSparkles,
  XCircle,
} from "lucide-react";
import { generateContent } from "../services/api/contentService";
import type {
  ContentGenerationRequest,
  ContentStyle,
  Platform,
} from "../types/content";

const styles: ContentStyle[] = [
  "Educational",
  "Promotional",
  "Entertainment",
  "News",
  "Storytelling",
];

const platforms: Platform[] = [
  "TikTok",
  "Instagram Reels",
  "YouTube Shorts",
  "Facebook",
];

export default function CreateContent() {
  const location = useLocation();
  const navigate = useNavigate();

  const [topic, setTopic] = useState("");
  const [style, setStyle] = useState<ContentStyle>("Educational");
  const [platform, setPlatform] = useState<Platform>("TikTok");
  const [duration, setDuration] = useState(45);
  const [targetAudience, setTargetAudience] = useState("");
  const [status, setStatus] = useState<"idle" | "generating" | "error">("idle");
  const [error, setError] = useState("");

  useEffect(() => {
    const incomingTopic = location.state?.topic;
    if (incomingTopic && typeof incomingTopic === "string") {
      setTopic(incomingTopic);
    }
  }, [location.state]);

  const canGenerate = topic.trim().length >= 3 && targetAudience.trim().length >= 2;

  const handleGenerate = async () => {
    if (!canGenerate) {
      setError("Add a topic and target audience before generating.");
      return;
    }

    setStatus("generating");
    setError("");

    const request: ContentGenerationRequest = {
      topic,
      style,
      platform,
      duration,
      targetAudience,
    };

    try {
      const content = await generateContent(request);
      navigate("/content-results", { state: { content } });
    } catch (err) {
      setStatus("error");
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setStatus((current) => (current === "generating" ? "idle" : current));
    }
  };

  return (
    <div className="mx-auto max-w-5xl px-6 py-7">
      <div className="mb-8">
        <div className="mb-3 flex items-center gap-2 text-xs font-medium text-slate-400">
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-slate-900 text-white">
            1
          </span>
          Idea
          <span className="h-px w-8 bg-slate-200" />
          <span className="flex h-6 w-6 items-center justify-center rounded-full border border-slate-200">
            2
          </span>
          Settings
          <span className="h-px w-8 bg-slate-200" />
          <span className="flex h-6 w-6 items-center justify-center rounded-full border border-slate-200">
            3
          </span>
          Generate
        </div>

        <h1 className="text-3xl font-semibold tracking-tight text-slate-950">
          Create a video
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
          Turn a simple idea into a complete short-form video concept with an
          AI-written hook, script, caption and hashtags.
        </p>
      </div>

      <div className="grid gap-5 lg:grid-cols-[1.25fr_0.75fr]">
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-6 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100">
              <Sparkles className="h-5 w-5 text-slate-700" />
            </div>
            <div>
              <h2 className="font-semibold text-slate-900">Video idea</h2>
              <p className="text-xs text-slate-500">
                Start with a topic, product or problem.
              </p>
            </div>
          </div>

          <label className="mb-2 block text-sm font-medium text-slate-700">
            What do you want to create?
          </label>
          <textarea
            value={topic}
            onChange={(event) => setTopic(event.target.value)}
            placeholder="e.g. 5 ways small businesses can use AI to save time"
            rows={5}
            className="w-full resize-none rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-400 focus:bg-white focus:ring-2 focus:ring-slate-100"
          />

          <div className="mt-6">
            <label className="mb-2 block text-sm font-medium text-slate-700">
              Content style
            </label>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
              {styles.map((item) => (
                <button
                  key={item}
                  onClick={() => setStyle(item)}
                  className={`rounded-xl border px-3 py-3 text-xs font-medium transition ${
                    style === item
                      ? "border-slate-900 bg-slate-900 text-white"
                      : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  {style === item && <Check className="mx-auto mb-1 h-3.5 w-3.5" />}
                  {item}
                </button>
              ))}
            </div>
          </div>

          <div className="mt-6 grid gap-5 sm:grid-cols-2">
            <div>
              <label className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-700">
                <Target className="h-4 w-4 text-slate-400" />
                Platform
              </label>
              <select
                value={platform}
                onChange={(event) => setPlatform(event.target.value as Platform)}
                className="w-full rounded-xl border border-slate-200 bg-white px-3 py-3 text-sm text-slate-700 outline-none focus:border-slate-400"
              >
                {platforms.map((item) => (
                  <option key={item}>{item}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-700">
                <Clock3 className="h-4 w-4 text-slate-400" />
                Duration
              </label>
              <select
                value={duration}
                onChange={(event) => setDuration(Number(event.target.value))}
                className="w-full rounded-xl border border-slate-200 bg-white px-3 py-3 text-sm text-slate-700 outline-none focus:border-slate-400"
              >
                <option value={15}>15 seconds</option>
                <option value={30}>30 seconds</option>
                <option value={45}>45 seconds</option>
                <option value={60}>60 seconds</option>
                <option value={90}>90 seconds</option>
              </select>
            </div>
          </div>

          <div className="mt-6">
            <label className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-700">
              <Users className="h-4 w-4 text-slate-400" />
              Target audience
            </label>
            <input
              value={targetAudience}
              onChange={(event) => setTargetAudience(event.target.value)}
              placeholder="e.g. young entrepreneurs in Africa"
              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none focus:border-slate-400 focus:bg-white focus:ring-2 focus:ring-slate-100"
            />
          </div>

          {error && (
            <div className="mt-5 flex items-start gap-2 rounded-xl border border-red-100 bg-red-50 p-3 text-sm text-red-700">
              <XCircle className="mt-0.5 h-4 w-4 shrink-0" />
              {error}
            </div>
          )}

          <button
            onClick={handleGenerate}
            disabled={status === "generating"}
            className="mt-7 flex w-full items-center justify-center gap-2 rounded-xl bg-slate-900 px-5 py-3.5 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {status === "generating" ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Generating your content...
              </>
            ) : (
              <>
                <WandSparkles className="h-4 w-4" />
                Generate AI Content
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </button>
        </section>

        <aside className="space-y-5">
          <div className="rounded-2xl border border-slate-200 bg-slate-950 p-6 text-white shadow-sm">
            <Sparkles className="mb-5 h-6 w-6 text-slate-300" />
            <h2 className="text-lg font-semibold">What you'll get</h2>
            <div className="mt-5 space-y-4">
              {[
                ["Hook", "A strong opening designed to stop the scroll."],
                ["Script", "A structured script matched to your duration."],
                ["Caption", "A ready-to-publish social caption."],
                ["Hashtags", "Relevant discovery hashtags."],
                ["Ideas", "Five follow-up video concepts."],
              ].map(([title, description]) => (
                <div key={title} className="flex gap-3">
                  <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-white/10">
                    <Check className="h-3.5 w-3.5" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">{title}</p>
                    <p className="mt-0.5 text-xs leading-5 text-slate-400">
                      {description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-slate-500" />
              <p className="text-sm font-semibold text-slate-900">
                Next step
              </p>
            </div>
            <p className="mt-2 text-xs leading-5 text-slate-500">
              After generation, you'll review the content and send it directly
              into the storyboard workflow.
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}
