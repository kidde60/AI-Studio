import { useState } from "react";
import { ArrowRight, Check, LoaderCircle, Sparkles } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import { generateContent } from "../../services/api/contentService";
import type { ContentStyle, Platform } from "../../types/content";

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

const durations = [
  { label: "30 seconds", value: 30 },
  { label: "60 seconds", value: 60 },
  { label: "90 seconds", value: 90 },
];

export function CreateContent() {
  const location = useLocation();
  const navigate = useNavigate();

  const initialTopic = (location.state as { topic?: string } | null)?.topic ?? "";

  const [style, setStyle] = useState<ContentStyle>("Educational");
  const [platform, setPlatform] = useState<Platform>("TikTok");
  const [topic, setTopic] = useState(initialTopic);
  const [duration, setDuration] = useState(30);
  const [targetAudience, setTargetAudience] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState("");

  const handleGenerate = async () => {
    const trimmedTopic = topic.trim();

    if (trimmedTopic.length < 3) {
      setError("Please enter a topic or idea with at least 3 characters.");
      return;
    }

    setError("");
    setIsGenerating(true);

    try {
      const content = await generateContent({
        topic: trimmedTopic,
        style,
        platform,
        duration,
        targetAudience: targetAudience.trim() || "General audience",
      });

      navigate("/content-results", { state: { content } });
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong while generating your content.",
      );
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      <div>
        <p className="mb-2 flex items-center gap-2 text-sm font-semibold text-accent">
          <Sparkles size={15} />
          AI Content Generator
        </p>
        <h1 className="text-3xl font-bold tracking-tight">
          What do you want to create?
        </h1>
        <p className="mt-2 text-sm text-muted">
          Start with a topic, product, keyword or rough idea.
        </p>
      </div>

      <div className="panel p-6 md:p-8">
        <label className="text-sm font-semibold">Topic or idea</label>
        <textarea
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          className="input mt-3 min-h-32 resize-none"
          placeholder="e.g. 5 reasons businesses should invest in digital transformation..."
          disabled={isGenerating}
        />

        <div className="mt-8">
          <label className="text-sm font-semibold">Content style</label>
          <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            {styles.map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => setStyle(item)}
                disabled={isGenerating}
                className={`rounded-xl border p-3 text-left text-sm ${
                  style === item
                    ? "border-ink bg-neutral-50 font-semibold"
                    : "border-line hover:bg-neutral-50"
                }`}
              >
                <span
                  className={`mb-3 flex h-7 w-7 items-center justify-center rounded-lg ${
                    style === item
                      ? "bg-ink text-white"
                      : "bg-neutral-100 text-neutral-500"
                  }`}
                >
                  {style === item && <Check size={14} />}
                </span>
                {item}
              </button>
            ))}
          </div>
        </div>

        <div className="mt-8">
          <label className="text-sm font-semibold">Platform</label>
          <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {platforms.map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => setPlatform(item)}
                disabled={isGenerating}
                className={`rounded-xl border px-4 py-3 text-left text-sm ${
                  platform === item
                    ? "border-ink bg-neutral-50 font-semibold"
                    : "border-line hover:bg-neutral-50"
                }`}
              >
                {item}
              </button>
            ))}
          </div>
        </div>

        <div className="mt-8 grid gap-4 md:grid-cols-2">
          <div>
            <label className="text-sm font-semibold">Duration</label>
            <select
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              className="input mt-3"
              disabled={isGenerating}
            >
              {durations.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-sm font-semibold">Target audience</label>
            <input
              value={targetAudience}
              onChange={(e) => setTargetAudience(e.target.value)}
              className="input mt-3"
              placeholder="e.g. Business owners"
              disabled={isGenerating}
            />
          </div>
        </div>

        {error && (
          <div
            role="alert"
            className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
          >
            {error}
          </div>
        )}

        <div className="mt-8 flex flex-col justify-between gap-4 border-t border-line pt-6 sm:flex-row sm:items-center">
          <div className="text-xs text-muted">
            <span className="font-semibold text-ink">{style}</span> · {platform} ·{" "}
            {duration}s
          </div>

          <button
            type="button"
            onClick={handleGenerate}
            disabled={isGenerating}
            className="btn-primary disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isGenerating ? (
              <>
                <LoaderCircle size={17} className="animate-spin" />
                Generating with Gemini...
              </>
            ) : (
              <>
                <Sparkles size={17} />
                Generate Content
                <ArrowRight size={17} />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default CreateContent;
