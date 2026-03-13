// frontend/src/features/feed/components/XPanel.tsx

import { useState, useMemo } from "react"
import type { FeedItem } from "../../../shared/types"

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
        <a key={key++} href={part}
          onClick={async e => { e.stopPropagation(); e.preventDefault(); await openUrl(part) }}
          className="underline transition-colors duration-150"
          style={{ color: "var(--accent-x)" }}
          onMouseEnter={e => (e.currentTarget.style.color = "var(--accent-green)")}
          onMouseLeave={e => (e.currentTarget.style.color = "var(--accent-x)")}
        >{part}</a>
      )
    }
    return <span key={key++}>{part}</span>
  })
}

// ── Avatar ────────────────────────────────────────────────────────────────────

function HandleAvatar({ avatar, handle, size = 36 }: { avatar: string; handle: string; size?: number }) {
  const [err, setErr] = useState(false)

  if (avatar && !err) {
    return (
      <img src={avatar} alt={handle} onError={() => setErr(true)}
        className="rounded-full object-cover flex-shrink-0"
        style={{ width: size, height: size, border: "1px solid var(--border)" }}
      />
    )
  }
  return (
    <div className="rounded-full flex items-center justify-center flex-shrink-0 font-bold uppercase"
      style={{
        width: size, height: size, fontSize: size * 0.35,
        background: "rgba(255,255,255,0.06)", border: "1px solid var(--border)",
        color: "var(--muted)", fontFamily: "JetBrains Mono, monospace",
      }}
    >
      {handle[0]}
    </div>
  )
}

// ── Account row ───────────────────────────────────────────────────────────────

function AccountRow({ handle, avatar, count, latest, onClick, index }: {
  handle: string; avatar: string; count: number; latest: string;
  onClick: () => void; index: number
}) {
  return (
    <div
      onClick={onClick}
      className="group flex items-center gap-3 p-3 cursor-pointer transition-all duration-150"
      style={{
        borderBottom:   "1px solid var(--border)",
        background:     "var(--bg)",
        animation:      "fadeIn 0.2s ease both",
        animationDelay: `${Math.min(index * 40, 400)}ms`,
      }}
      onMouseEnter={e => (e.currentTarget.style.background = "rgba(255,255,255,0.03)")}
      onMouseLeave={e => (e.currentTarget.style.background = "var(--bg)")}
    >
      <HandleAvatar avatar={avatar} handle={handle} size={40} />

      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <span className="text-[12px] font-semibold"
            style={{ color: "var(--text)", fontFamily: "JetBrains Mono, monospace" }}
          >
            @{handle}
          </span>
          <span className="text-[10px]" style={{ color: "var(--muted)" }}>
            {fmtRelative(latest)}
          </span>
        </div>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-[9px] uppercase tracking-widest px-1.5 py-px rounded-sm"
            style={{ background: "rgba(255,255,255,0.06)", color: "var(--muted)" }}
          >
            {count} tweets
          </span>
          <span className="text-[9px] uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-opacity"
            style={{ color: "var(--accent-green)" }}
          >
            view feed →
          </span>
        </div>
      </div>
    </div>
  )
}

// ── Tweet card ────────────────────────────────────────────────────────────────

function TweetCard({ item, index }: { item: FeedItem; index: number }) {

  const [qImgErr, setQImgErr]     = useState(false)
  const quoteImg    = item.quote_img    ?? ""
  const quoteAuthor = item.quote_author ?? ""

  // split main tweet text from quoted block
  // desc_clean includes the quoted author name and text after a blank line
  const fullText  = item.description || item.title
  const lines     = fullText.split("\n")
  const quoteIdx  = quoteAuthor
    ? lines.findIndex(l => l.includes(quoteAuthor))
    : -1
  const mainText  = quoteIdx > 0 ? lines.slice(0, quoteIdx).join("\n").trim() : fullText
  const quoteText = quoteIdx >= 0 ? lines.slice(quoteIdx + 1).join("\n").trim() : ""

  return (
    <div
      onClick={() => openUrl(item.url)}
      className="flex gap-3 p-3 cursor-pointer transition-all duration-150"
      style={{
        borderBottom:   "1px solid var(--border)",
        background:     "var(--bg)",
        animation:      "fadeIn 0.2s ease both",
        animationDelay: `${Math.min(index * 20, 300)}ms`,
      }}
      onMouseEnter={e => (e.currentTarget.style.background = "rgba(255,255,255,0.03)")}
      onMouseLeave={e => (e.currentTarget.style.background = "var(--bg)")}
    >
      <HandleAvatar avatar={item.avatar} handle={item.author} size={36} />

      <div className="flex-1 min-w-0 flex flex-col gap-1.5">
        {/* author + time */}
        <div className="flex items-center justify-between gap-2">
          <span className="text-[11px] font-semibold truncate"
            style={{ color: "var(--text)", fontFamily: "JetBrains Mono, monospace" }}
          >
            @{item.author}
          </span>
          <span className="text-[10px] flex-shrink-0" style={{ color: "var(--muted)" }}>
            {fmtRelative(item.published)}
          </span>
        </div>

        {/* main tweet text */}
        <p className="text-[12px] leading-relaxed break-words"
          style={{ color: "var(--text)", whiteSpace: "pre-wrap", wordBreak: "break-word" }}
        >
          {parseLinks(mainText)}
        </p>

        {/* quoted block */}
        {(quoteText || quoteImg) && (
          <div className="flex flex-col gap-1.5 p-2 mt-0.5"
            style={{
              border:     "1px solid var(--border)",
              background: "rgba(255,255,255,0.03)",
              borderLeft: "2px solid var(--accent-x)",
            }}
          >
            {quoteAuthor && (
              <span className="text-[10px] font-semibold"
                style={{ color: "var(--accent-x)", fontFamily: "JetBrains Mono, monospace" }}
              >
                {quoteAuthor}
              </span>
            )}
            {quoteText && (
              <p className="text-[11px] leading-relaxed break-words line-clamp-4"
                style={{ color: "var(--muted)", whiteSpace: "pre-wrap", wordBreak: "break-word" }}
              >
                {parseLinks(quoteText)}
              </p>
            )}
            {quoteImg && !qImgErr && (
              <img src={quoteImg} alt="" onError={() => setQImgErr(true)}
                className="w-full rounded-sm object-contain mt-1"
                style={{ border: "1px solid var(--border)", maxHeight: 200 }}
              />
            )}
          </div>
        )}

        {/* timestamp */}
        <span className="text-[9px]" style={{ color: "var(--muted)" }}>
          {fmtFull(item.published)}
        </span>
      </div>
    </div>
  )
}

// ── Main export ───────────────────────────────────────────────────────────────

type XView = 'accounts' | 'feed'

export default function XPanel({ items, loading }: { items: FeedItem[]; loading: boolean }) {
  const [view, setView]               = useState<XView>('feed')
  const [activeHandle, setActiveHandle] = useState<string | null>(null)

  const accounts = useMemo(() => {
    const seen: Record<string, { avatar: string; count: number; latest: string }> = {}
    for (const item of items) {
      if (!seen[item.author]) seen[item.author] = { avatar: item.avatar, count: 0, latest: item.published }
      seen[item.author].count++
      if (item.published > seen[item.author].latest)
        seen[item.author].latest = item.published
    }
    return Object.entries(seen)
      .map(([handle, v]) => ({ handle, ...v }))
      .sort((a, b) => b.latest > a.latest ? 1 : -1)
  }, [items])

  const filtered = useMemo(
    () => activeHandle ? items.filter(i => i.author === activeHandle) : items,
    [items, activeHandle]
  )

  if (loading) return (
    <div className="flex-1 flex items-center justify-center gap-3">
      <span className="inline-block w-4 h-4 rounded-full border-2 animate-spin"
        style={{ borderColor: "var(--border)", borderTopColor: "var(--accent-x)" }}
      />
      <p className="text-xs" style={{ color: "var(--muted)" }}>Fetching X...</p>
    </div>
  )

  if (items.length === 0) return (
    <div className="flex-1 flex flex-col items-center justify-center gap-3 px-6">
      <span className="text-3xl opacity-10">𝕏</span>
      <p className="text-[11px] text-center leading-relaxed" style={{ color: "var(--muted)" }}>
        Set <code style={{ color: "var(--accent-green)" }}>X_HANDLES</code> in{" "}
        <code style={{ color: "var(--accent-green)" }}>backend/.env</code> to enable
      </p>
    </div>
  )

  return (
    <div className="flex-1 flex flex-col min-h-0">

      {/* ── top tab bar ── */}
      <div className="flex items-center gap-2 px-3 py-2 flex-shrink-0"
        style={{ borderBottom: "1px solid var(--border)", background: "var(--bg2)" }}
      >
        {(["feed", "accounts"] as XView[]).map(v => (
          <button key={v} onClick={() => setView(v)}
            className="px-3 py-1 text-[10px] uppercase tracking-widest rounded-sm transition-all duration-150"
            style={{
              fontFamily: "JetBrains Mono, monospace",
              border:     `1px solid ${view === v ? "var(--accent-x)" : "var(--border)"}`,
              background: view === v ? "rgba(255,255,255,0.06)" : "transparent",
              color:      view === v ? "var(--text)" : "var(--muted)",
              cursor:     "pointer",
            }}
          >
            {v === 'feed' ? `feed ${activeHandle ? `· @${activeHandle}` : `· ${items.length}`}` : `accounts · ${accounts.length}`}
          </button>
        ))}

        {/* clear filter pill */}
        {activeHandle && view === 'feed' && (
          <button onClick={() => setActiveHandle(null)}
            className="ml-auto text-[9px] uppercase tracking-widest px-2 py-1 rounded-sm transition-all"
            style={{
              fontFamily: "JetBrains Mono, monospace",
              border: "1px solid var(--border)", color: "var(--muted)",
              background: "transparent", cursor: "pointer",
            }}
            onMouseEnter={e => (e.currentTarget.style.color = "#ff4444")}
            onMouseLeave={e => (e.currentTarget.style.color = "var(--muted)")}
          >
            ✕ clear filter
          </button>
        )}
      </div>

      {/* ── accounts view ── */}
      {view === 'accounts' && (
        <div className="flex-1 overflow-y-auto min-h-0">
          {accounts.map(({ handle, avatar, count, latest }, idx) => (
            <AccountRow
              key={handle} handle={handle} avatar={avatar}
              count={count} latest={latest} index={idx}
              onClick={() => { setActiveHandle(handle); setView('feed') }}
            />
          ))}
        </div>
      )}

      {/* ── feed view ── */}
      {view === 'feed' && (
        <div className="flex-1 overflow-y-auto min-h-0">
          {filtered.map((item, idx) => (
            <TweetCard key={item.id} item={item} index={idx} />
          ))}
        </div>
      )}
    </div>
  )
}