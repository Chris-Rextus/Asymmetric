// frontend/src/features/feed/components/RedditPanel.tsx

import { useState, useEffect } from "react"
import type { FeedItem } from "../../../shared/types"

interface Subreddit {
  subreddit:        string
  post_count:       number
  latest_published: string
  latest_title:     string
  icon:             string
}

// ── Helpers ───────────────────────────────────────────────────────────────────


function fmtRelative(iso: string): string {
  try {
    const diffMs = Date.now() - new Date(iso).getTime()
    const diffH  = diffMs / 1000 / 3600
    if (diffH < 1)   return `${Math.floor(diffMs / 60000)}m ago`
    if (diffH < 24)  return `${Math.floor(diffH)}h ago`
    if (diffH < 168) return `${Math.floor(diffH / 24)}d ago`
    return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric" })
  } catch { return iso }
}


function fmtFull(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("en-US", {
      month: "short", day: "numeric", year: "numeric",
      hour: "2-digit", minute: "2-digit",
    })
  } catch { return iso }
}

async function openUrl(url: string) {
  await fetch(`/api/open?url=${encodeURIComponent(url)}`)
}

function parseLinks(text: string): React.ReactNode[] {
  const urlRegex = /(https?:\/\/[^\s]+)/g
  const parts    = text.split(urlRegex)
  let   key      = 0
  return parts.map(part => {
    if (urlRegex.test(part)) {
      return (
        <a
          key={key++}
          href={part}
          onClick={async e => { e.stopPropagation(); e.preventDefault(); await openUrl(part) }}
          className="underline transition-colors duration-150"
          style={{ color: "#ff6314" }}
          onMouseEnter={e => (e.currentTarget.style.color = "var(--accent-green)")}
          onMouseLeave={e => (e.currentTarget.style.color = "#ff6314")}
        >
          {part}
        </a>
      )
    }
    return <span key={key++}>{part}</span>
  })
}

// ── Subreddit avatar ──────────────────────────────────────────────────────────

function SubredditAvatar({ avatar, name, size = 44 }: { avatar: string; name: string; size?: number }) {
  const [err, setErr] = useState(false)

  if (avatar && !err) {
    return (
      <img
        src={avatar}
        alt={name}
        onError={() => setErr(true)}
        className="rounded-full object-cover flex-shrink-0"
        style={{ width: size, height: size, border: "1px solid var(--border)" }}
      />
    )
  }

  return (
    <div
      className="rounded-full flex items-center justify-center flex-shrink-0 font-bold"
      style={{
        width:      size,
        height:     size,
        fontSize:   size * 0.28,
        background: "rgba(255,99,20,0.15)",
        border:     "1px solid rgba(255,99,20,0.3)",
        color:      "#ff6314",
        fontFamily: "JetBrains Mono, monospace",
      }}
    >
      r/
    </div>
  )
}

// ── Subreddit card ────────────────────────────────────────────────────────────

function SubredditCard({ sub, index, onClick }: { sub: Subreddit; index: number; onClick: () => void }) {
  return (
    <div
      onClick={onClick}
      className="group flex items-start gap-3 p-3 cursor-pointer transition-all duration-150"
      style={{
        borderBottom:   "1px solid var(--border)",
        background:     "var(--bg)",
        animation:      "fadeIn 0.25s ease both",
        animationDelay: `${Math.min(index * 40, 400)}ms`,
      }}
      onMouseEnter={e => (e.currentTarget.style.background = "rgba(255,99,20,0.04)")}
      onMouseLeave={e => (e.currentTarget.style.background = "var(--bg)")}
    >
      <SubredditAvatar avatar={sub.icon} name={sub.subreddit} size={44} />

      <div className="flex-1 min-w-0 flex flex-col gap-1">
        <div className="flex items-center justify-between gap-2">
          <span
            className="text-[12px] font-semibold truncate"
            style={{ color: "var(--text)", fontFamily: "JetBrains Mono, monospace" }}
          >
            r/{sub.subreddit}
          </span>
          <span className="text-[10px] flex-shrink-0" style={{ color: "var(--muted)" }}>
            {fmtRelative(sub.latest_published)}
          </span>
        </div>

        <p className="text-[11px] leading-snug line-clamp-2" style={{ color: "var(--muted)" }}>
          {sub.latest_title}
        </p>

        <div className="flex items-center gap-2 mt-0.5">
          <span
            className="text-[9px] uppercase tracking-widest px-1.5 py-px rounded-sm"
            style={{ background: "rgba(255,99,20,0.12)", color: "#ff6314" }}
          >
            {sub.post_count} posts
          </span>
          <span
            className="text-[9px] uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-opacity"
            style={{ color: "var(--accent-green)" }}
          >
            open →
          </span>
        </div>
      </div>
    </div>
  )
}

// ── Post card ─────────────────────────────────────────────────────────────────

function PostCard({ item, index }: { item: FeedItem; index: number }) {
  const [imgErr, setImgErr] = useState(false)
  const thumbnail = (item as any).thumbnail as string
  const score     = (item as any).score as number
  const comments  = (item as any).num_comments as number
  const domain    = (item as any).domain as string

  return (
    <div
      onClick={() => openUrl(item.url)}
      className="flex flex-col gap-2 p-3 cursor-pointer transition-all duration-150"
      style={{
        borderBottom:   "1px solid var(--border)",
        background:     "var(--bg)",
        animation:      "fadeIn 0.2s ease both",
        animationDelay: `${Math.min(index * 25, 300)}ms`,
      }}
      onMouseEnter={e => (e.currentTarget.style.background = "rgba(255,99,20,0.04)")}
      onMouseLeave={e => (e.currentTarget.style.background = "var(--bg)")}
    >
      {/* accent bar */}
      <div className="h-[1px] w-full" style={{ background: "rgba(255,99,20,0.3)" }} />

      {/* thumbnail */}
      {thumbnail && !imgErr && (
        <img
          src={thumbnail}
          alt=""
          onError={() => setImgErr(true)}
          className="w-full rounded-sm object-contain"
          style={{ border: "1px solid var(--border)" }}
        />
      )}

      {/* title */}
      <p
        className="text-[12px] font-semibold leading-snug"
        style={{ color: "var(--text)", fontFamily: "JetBrains Mono, monospace" }}
      >
        {item.title}
      </p>

      {/* body text if any */}
      {item.description && item.description !== item.title && (
        <p
          className="text-[11px] leading-relaxed break-words line-clamp-3"
          style={{ color: "var(--muted)", whiteSpace: "pre-wrap", wordBreak: "break-word" }}
        >
          {parseLinks(item.description)}
        </p>
      )}

      {/* meta row */}
      <div
        className="flex items-center gap-3 pt-1.5 flex-wrap"
        style={{ borderTop: "1px solid var(--border)" }}
      >
        {domain && (
          <span className="text-[9px] uppercase tracking-widest" style={{ color: "var(--muted)" }}>
            {domain}
          </span>
        )}
        {score !== undefined && (
          <span className="text-[9px] uppercase tracking-widest" style={{ color: "#ff6314" }}>
            ▲ {score.toLocaleString()}
          </span>
        )}
        {comments !== undefined && (
          <span className="text-[9px] uppercase tracking-widest" style={{ color: "var(--muted)" }}>
            💬 {comments.toLocaleString()}
          </span>
        )}
        <span className="text-[9px] ml-auto" style={{ color: "var(--muted)" }}>
          {fmtFull(item.published)}
        </span>
      </div>
    </div>
  )
}

// ── Main export ───────────────────────────────────────────────────────────────

export default function RedditPanel({ items, loading }: { items: FeedItem[]; loading: boolean }) {

  const [selected, setSelected] = useState<Subreddit | null>(null)
  const [subreddits, setSubreddits] = useState<Subreddit[]>([])

  useEffect(() => {
    if (items.length === 0) return
    const seen: Record<string, Subreddit> = {}
    for (const item of items) {
      const sub = (item as any).subreddit as string
      if (!sub) continue
      if (!seen[sub]) {
        seen[sub] = {
          subreddit:        sub,
          icon:             item.avatar ?? "",
          post_count:       0,
          latest_published: item.published,
          latest_title:     item.title,
        }
      }
      seen[sub].post_count++
      if (item.published > seen[sub].latest_published) {
        seen[sub].latest_published = item.published
        seen[sub].latest_title     = item.title
      }
    }
    setSubreddits(
      Object.values(seen).sort((a, b) => b.latest_published > a.latest_published ? 1 : -1)
    )
  }, [items])

  const posts = selected
    ? items.filter(i => (i as any).subreddit === selected.subreddit)
    : []

  // loading
  if (loading) return (
    <div className="flex-1 flex items-center justify-center gap-3">
      <span
        className="inline-block w-4 h-4 rounded-full border-2 animate-spin"
        style={{ borderColor: "var(--border)", borderTopColor: "#ff6314" }}
      />
      <p className="text-xs" style={{ color: "var(--muted)" }}>Fetching Reddit...</p>
    </div>
  )

  // empty
  if (subreddits.length === 0) return (
    <div className="flex-1 flex flex-col items-center justify-center gap-3 px-6">
      <span className="text-3xl opacity-10">🤖</span>
      <p className="text-[11px] text-center leading-relaxed" style={{ color: "var(--muted)" }}>
        No subreddits yet. Set <code style={{ color: "var(--accent-green)" }}>REDDIT_SUBREDDITS</code> in{" "}
        <code style={{ color: "var(--accent-green)" }}>backend/.env</code>
      </p>
    </div>
  )

  // subreddit list
  if (!selected) return (
    <div className="flex-1 overflow-y-auto min-h-0">
      {subreddits.map((sub, idx) => (
        <SubredditCard key={sub.subreddit} sub={sub} index={idx} onClick={() => setSelected(sub)} />
      ))}
    </div>
  )

  // post list
  return (
    <div className="flex-1 flex flex-col min-h-0" style={{ animation: "slideIn 0.2s ease both" }}>

      {/* back bar */}
      <div
        className="px-3 py-2 flex items-center gap-3 flex-shrink-0"
        style={{ borderBottom: "1px solid var(--border)", background: "var(--bg2)" }}
      >
        <button
          onClick={() => setSelected(null)}
          className="text-[10px] uppercase tracking-widest transition-colors"
          style={{
            color: "var(--muted)", fontFamily: "JetBrains Mono, monospace",
            background: "transparent", border: "none", cursor: "pointer", padding: "4px 8px",
          }}
          onMouseEnter={e => (e.currentTarget.style.color = "#ff6314")}
          onMouseLeave={e => (e.currentTarget.style.color = "var(--muted)")}
        >
          ← back
        </button>

        <div className="w-px h-4" style={{ background: "var(--border)" }} />

        <SubredditAvatar avatar={selected.icon} name={selected.subreddit} size={28} />

        <div className="flex flex-col min-w-0">
          <span
            className="text-[11px] font-semibold truncate"
            style={{ color: "var(--text)", fontFamily: "JetBrains Mono, monospace" }}
          >
            r/{selected.subreddit}
          </span>
          <span className="text-[9px]" style={{ color: "var(--muted)" }}>
            {posts.length} posts
          </span>
        </div>
      </div>

      {/* posts */}
      <div className="flex-1 overflow-y-auto min-h-0">
        {posts.map((item, idx) => (
          <PostCard key={item.id} item={item} index={idx} />
        ))}
      </div>

      <style>{`
        @keyframes slideIn {
          from { opacity: 0; transform: translateX(12px); }
          to   { opacity: 1; transform: translateX(0); }
        }
      `}</style>
    </div>
  )
}