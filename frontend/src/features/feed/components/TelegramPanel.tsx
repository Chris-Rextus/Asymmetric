// frontend/src/features/feed/components/TelegramPanel.tsx

import { useState, useEffect } from "react"
import type { FeedItem } from "../../../shared/types"

interface Channel {
  channel_id:       string
  name:             string
  avatar:           string
  message_count:    number
  latest_published: string
  latest_preview:   string
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

function proxyImg(url: string): string {
  if (!url) return ""
  return `/api/proxy/image?url=${encodeURIComponent(url)}`
}

function parseLinks(text: string): React.ReactNode[] {
  const urlRegex = /(https?:\/\/[^\s]+)/g
  const parts = text.split(urlRegex)
  let key = 0

  return parts.map(part => {
    if (urlRegex.test(part)) {
      return (
        <a
          key={key++}
          href={part}
          onClick={async e => {
            e.stopPropagation()
            e.preventDefault()
            await openUrl(part)
          }}
          className="underline transition-colors duration-150"
          style={{ color: "#29b6f6" }}
          onMouseEnter={e => (e.currentTarget.style.color = "var(--accent-green)")}
          onMouseLeave={e => (e.currentTarget.style.color = "#29b6f6")}
        >
          {part}
        </a>
      )
    }

    return <span key={key++}>{part}</span>
  })
}

// ── Avatar ────────────────────────────────────────────────────────────────────

function Avatar({ src, name, size = 44 }: { src: string; name: string; size?: number }) {
  const [err, setErr] = useState(false)
  if (src && !err) {
    return (
      <img
        src={src} alt={name} onError={() => setErr(true)}
        className="rounded-full object-cover flex-shrink-0"
        style={{ width: size, height: size, border: "1px solid var(--border)" }}
      />
    )
  }
  return (
    <div
      className="rounded-full flex items-center justify-center flex-shrink-0 font-bold"
      style={{
        width: size, height: size, fontSize: size * 0.25,
        background: "rgba(41,182,246,0.15)",
        border:     "1px solid rgba(41,182,246,0.3)",
        color:      "#29b6f6",
        fontFamily: "JetBrains Mono, monospace",
      }}
    >
      {name.slice(0, 2).toUpperCase()}
    </div>
  )
}

// ── Channel card ──────────────────────────────────────────────────────────────

function ChannelCard({ channel, index, onClick }: { channel: Channel; index: number; onClick: () => void }) {
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
      onMouseEnter={e => (e.currentTarget.style.background = "rgba(41,182,246,0.04)")}
      onMouseLeave={e => (e.currentTarget.style.background = "var(--bg)")}
    >
      <Avatar src={proxyImg(channel.avatar)} name={channel.name} size={44} />

      <div className="flex-1 min-w-0 flex flex-col gap-1">
        <div className="flex items-center justify-between gap-2">
          <span
            className="text-[12px] font-semibold truncate"
            style={{ color: "var(--text)", fontFamily: "JetBrains Mono, monospace" }}
          >
            {channel.name}
          </span>
          <span className="text-[10px] flex-shrink-0" style={{ color: "var(--muted)" }}>
            {fmtRelative(channel.latest_published)}
          </span>
        </div>

        <p className="text-[11px] leading-snug line-clamp-2" style={{ color: "var(--muted)" }}>
          {channel.latest_preview}
        </p>

        <div className="flex items-center gap-2 mt-0.5">
          <span
            className="text-[9px] uppercase tracking-widest px-1.5 py-px rounded-sm"
            style={{ background: "rgba(41,182,246,0.12)", color: "#29b6f6" }}
          >
            {channel.message_count} msgs
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

// ── Message card ──────────────────────────────────────────────────────────────

function MessageCard({ item, index }: { item: FeedItem; index: number }) {
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
      onMouseEnter={e => (e.currentTarget.style.background = "rgba(41,182,246,0.04)")}
      onMouseLeave={e => (e.currentTarget.style.background = "var(--bg)")}
    >
      <div className="h-[1px] w-full" style={{ background: "rgba(41,182,246,0.25)" }} />
      <p
        className="text-[12px] leading-relaxed break-words"
        style={{ color: "var(--text)", whiteSpace: "pre-wrap", wordBreak: "break-word" }}
      >
        {parseLinks(item.description || item.title)}
      </p>
      <p
        className="text-[10px] pt-1.5"
        style={{ color: "var(--muted)", borderTop: "1px solid var(--border)" }}
      >
        {fmtFull(item.published)}
      </p>
    </div>
  )
}

// ── Main export ───────────────────────────────────────────────────────────────

export default function TelegramPanel({ items, loading }: { items: FeedItem[]; loading: boolean }) {
  const [selected, setSelected] = useState<Channel | null>(null)
  const [channels, setChannels] = useState<Channel[]>([])

  useEffect(() => {
    if (items.length === 0) return
    const seen: Record<string, Channel> = {}
    for (const item of items) {
      const cid = (item as any).channel_id as string
      if (!cid) continue
      if (!seen[cid]) {
        seen[cid] = {
          channel_id:       cid,
          name:             item.author,
          avatar:           (item as any).avatar ?? "",
          message_count:    0,
          latest_published: item.published,
          latest_preview:   item.description ?? item.title,
        }
      }
      seen[cid].message_count++
      if (item.published > seen[cid].latest_published) {
        seen[cid].latest_published = item.published
        seen[cid].latest_preview   = item.description ?? item.title
      }
    }
    setChannels(
      Object.values(seen).sort((a, b) => b.latest_published > a.latest_published ? 1 : -1)
    )
  }, [items])

  const messages = selected
    ? items.filter(i => (i as any).channel_id === selected.channel_id)
    : []

  if (loading) return (
    <div className="flex-1 flex items-center justify-center gap-3">
      <span
        className="inline-block w-4 h-4 rounded-full border-2 animate-spin"
        style={{ borderColor: "var(--border)", borderTopColor: "#29b6f6" }}
      />
      <p className="text-xs" style={{ color: "var(--muted)" }}>Fetching Telegram...</p>
    </div>
  )

  if (channels.length === 0) return (
    <div className="flex-1 flex flex-col items-center justify-center gap-3 px-6">
      <span className="text-3xl opacity-10">✈</span>
      <p className="text-[11px] text-center leading-relaxed" style={{ color: "var(--muted)" }}>
        No channels yet. Set <code style={{ color: "var(--accent-green)" }}>TELEGRAM_CHANNEL_IDS</code> in{" "}
        <code style={{ color: "var(--accent-green)" }}>backend/.env</code>
      </p>
    </div>
  )

  if (!selected) return (
    <div className="flex-1 overflow-y-auto min-h-0">
      {channels.map((ch, idx) => (
        <ChannelCard key={ch.channel_id} channel={ch} index={idx} onClick={() => setSelected(ch)} />
      ))}
    </div>
  )

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
          onMouseEnter={e => (e.currentTarget.style.color = "#29b6f6")}
          onMouseLeave={e => (e.currentTarget.style.color = "var(--muted)")}
        >
          ← back
        </button>

        <div className="w-px h-4" style={{ background: "var(--border)" }} />

        <Avatar src={proxyImg(selected.avatar)} name={selected.name} size={28} />

        <div className="flex flex-col min-w-0">
          <span
            className="text-[11px] font-semibold truncate"
            style={{ color: "var(--text)", fontFamily: "JetBrains Mono, monospace" }}
          >
            {selected.name}
          </span>
          <span className="text-[9px]" style={{ color: "var(--muted)" }}>
            {messages.length} messages
          </span>
        </div>
      </div>

      {/* messages */}
      <div className="flex-1 overflow-y-auto min-h-0">
        {messages.map((item, idx) => (
          <MessageCard key={item.id} item={item} index={idx} />
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