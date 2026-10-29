import {
  ArrowRight,
  Clock3,
  Film,
  Plus,
  Sparkles,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";
import { Link } from "react-router-dom";

const projects = [
  ["5 Digital Transformation Mistakes", "TikTok", "Completed", "Today"],
  ["Water Conservation Campaign", "Instagram Reels", "Draft", "Yesterday"],
  ["Business Leadership Tips", "YouTube Shorts", "Generating", "2 days ago"],
];

const stats: Array<{
  label: string;
  value: string;
  icon: LucideIcon;
  note: string;
}> = [
  { label: "Videos created", value: "12", icon: Film, note: "+4 this month" },
  { label: "In progress", value: "3", icon: Clock3, note: "2 rendering now" },
  { label: "Content generated", value: "48", icon: TrendingUp, note: "+18% this month" },
];

export function Dashboard() {
  return (
    <div className="space-y-8">
      <section className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
        <div>
          <p className="mb-2 text-sm font-semibold text-accent">AI Video Studio</p>
          <h1 className="text-3xl font-bold tracking-tight md:text-4xl">
            Good afternoon, Sheila.
          </h1>
          <p className="mt-2 max-w-xl text-sm leading-6 text-muted">
            Turn an idea into a polished social video with AI-powered scripting,
            visuals, voice and captions.
          </p>
        </div>
        <Link to="/create" className="btn-primary">
          <Plus size={18} />
          Create New Video
        </Link>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        {stats.map(({ label, value, icon: Icon, note }) => (
          <div className="panel p-5" key={label}>
            <div className="flex justify-between text-sm text-muted">
              <span>{label}</span>
              <Icon size={18} />
            </div>
            <p className="mt-4 text-3xl font-bold">{value}</p>
            <p className="mt-1 text-xs text-muted">{note}</p>
          </div>
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.5fr_1fr]">
        <div className="panel overflow-hidden">
          <div className="flex items-center justify-between border-b border-line px-5 py-4">
            <div>
              <h2 className="font-semibold">Recent projects</h2>
              <p className="text-xs text-muted">Continue where you left off.</p>
            </div>
            <Link
              to="/projects"
              className="flex items-center gap-1 text-xs font-semibold text-muted"
            >
              View all <ArrowRight size={14} />
            </Link>
          </div>

          <div className="divide-y divide-line">
            {projects.map(([title, platform, status, date]) => (
              <div key={title} className="flex items-center gap-4 p-4">
                <div className="flex h-16 w-24 items-center justify-center rounded-xl bg-neutral-100">
                  <Film size={20} className="text-neutral-400" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold">{title}</p>
                  <p className="mt-1 text-xs text-muted">
                    {platform} · {date}
                  </p>
                </div>
                <span className="rounded-full bg-neutral-100 px-2.5 py-1 text-[11px] font-semibold text-neutral-600">
                  {status}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-2xl bg-ink p-6 text-white">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/10">
            <Sparkles size={19} />
          </div>
          <h2 className="mt-5 text-xl font-bold">Start with an idea.</h2>
          <p className="mt-2 text-sm leading-6 text-neutral-300">
            Give the AI a topic, product or keyword. We'll turn it into a hook,
            script, storyboard and video concept.
          </p>
          <Link
            to="/create"
            className="mt-6 inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-ink"
          >
            Generate content <ArrowRight size={16} />
          </Link>
        </div>
      </section>
    </div>
  );
}
