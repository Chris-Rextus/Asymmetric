// frontend/src/features/feed/components/NewsPanel.tsx

import { useState, useEffect, useMemo } from "react"

// ── Types ─────────────────────────────────────────────────────────────────────

interface NewsItem {
  id:           string
  title:        string
  description:  string
  thumbnail:    string
  url:          string
  published:    string
  source_name:  string
  source_id:    string
  category:     string
  score:        number
  keywords:     string[]
  topics:       string[]
  is_trending:  boolean
}

// ── Constants ─────────────────────────────────────────────────────────────────

const CATEGORY_META: Record<string, { label: string; color: string }> = {
  all:        { label: "All",        color: "#f0a500" },
  infosec:    { label: "Infosec",    color: "#ff4444" },
  tech:       { label: "Tech",       color: "#29b6f6" },
  government: { label: "Government", color: "var(--accent-green)" },
  mainstream: { label: "Mainstream", color: "#f0a500" },
  finance:    { label: "Finance",    color: "#26c6da" },
  politics:   { label: "Politics",   color: "#ab47bc" },
}

const TOPIC_META: Record<string, { label: string; color: string }> = {
  ransomware:     { label: "Ransomware",     color: "#ff4444" },
  vulnerability:  { label: "Vulnerability",  color: "#ff6b35" },
  breach:         { label: "Breach",         color: "#e53935" },
  malware:        { label: "Malware",        color: "#ff4444" },
  apt:            { label: "APT",            color: "#ab47bc" },
  phishing:       { label: "Phishing",       color: "#ffa726" },
  critical_infra: { label: "Critical Infra", color: "#ef5350" },
  cloud:          { label: "Cloud",          color: "#29b6f6" },
  ai_security:    { label: "AI Security",    color: "#26c6da" },
  privacy:        { label: "Privacy",        color: "#66bb6a" },
  crypto:         { label: "Crypto",         color: "#f0a500" },
  geopolitics:    { label: "Geopolitics",    color: "#ab47bc" },
  exploit:        { label: "Exploit",        color: "#ff5252" },
  mobile:         { label: "Mobile",         color: "#29b6f6" },
  supply_chain:   { label: "Supply Chain",   color: "#ffa726" },
  regulation:     { label: "Regulation",     color: "var(--accent-green)" },
  usa:           { label: "USA",          color: "#29b6f6" },
  china:         { label: "China",        color: "#ff4444" },
  russia:        { label: "Russia",       color: "#ffa726" },
  europe:        { label: "Europe",       color: "#26c6da" },
  middleeast:    { label: "Middle East",  color: "#f0a500" },
  nuclear:       { label: "Nuclear",      color: "#ff5252" },
}

const CATEGORY_TOPICS: Record<string, string[]> = {
  all:        Object.keys(TOPIC_META),
  infosec:    ["ransomware", "vulnerability", "breach", "malware", "apt", "phishing", "critical_infra", "cloud", "ai_security", "exploit", "mobile", "supply_chain"],
  tech:       ["ai_security", "cloud", "mobile", "privacy", "crypto", "supply_chain", "regulation"],
  mainstream: ["usa", "china", "russia", "europe", "middleeast", "geopolitics", "war", "nuclear", "elections", "privacy", "regulation"],
  government: ["critical_infra", "regulation", "sanctions", "nuclear", "usa", "china", "russia", "europe", "war"],
  finance:    ["inflation", "central_banks", "trade", "sanctions", "crypto", "regulation", "usa", "china", "europe", "energy"],
  politics:   ["usa", "china", "russia", "europe", "middleeast", "geopolitics", "war", "nuclear", "elections", "sanctions", "energy"],
}

const SOURCE_INITIALS: Record<string, string> = {
  krebs:           "KRB",  bleepingcomputer: "BCP",
  thehackernews:   "THN",  darkreading:      "DR",
  schneier:        "SCH",  recordedfuture:   "RF",
  threatpost:      "TP",   wired:            "WRD",
  arstechnica:     "ARS",  theregister:      "REG",
  zdnet:           "ZDN",  reuters:          "REU",
  bbc:             "BBC",  guardian:         "GRD",
  ap:              "AP",   cisa:             "CISA",
  ncsc:            "NCSC", msrc:             "MSRC",
  enisa:           "ENISA",securityweek:     "SW",
  troyhunt:        "TH",   malwarebytes:     "MB",
  sophos:          "SPH",  crowdstrike:      "CS",
  sentinelone:     "S1",   checkpointres:    "CPR",
  unit42:          "U42",  googleprojectzero:"GPZ",
  mandiant:        "MAN",  exploitdb:        "EDB",
  packetstorm:     "PSS",  techcrunch:       "TC",
  hackernews_yc:   "HN",   technologyreview: "MTR",
  verge:           "VRG",  nyttech:          "NYT",
  wapotech:        "WPO",  ft:               "FT",
  nist_nvd:        "NVD",  cisa_ics:         "ICS",
  fbi:             "FBI",  austracyber:      "ASD",
  reuters_finance: "REF", cnbc:          "CNBC", ft_world:     "FTW",
  project_syndicate:"PS", vox_econ:      "VOX",  nber:         "NBER",
  worldbank:       "WB",  ecb:           "ECB",  axios:        "AXS",
  pbs_newshour:    "PBS", aljazeera:     "AJZ",  dw_news:      "DW",
  france24:        "F24", rferl:         "RFE",  euractiv:     "EUR",
  chathamhouse:    "CH",  stimson:       "STM",  crisisgroup:  "CG",
  sipri:           "SIP", iiss:          "IISS", understandingwar:"ISW",
  kyivindependent: "KYV", meduza:        "MDZ",  scmp:         "SCMP",
  nikkei:          "NKK", thediplomat:   "DIP",  asiatimes:    "AT",
  middleeasteye:   "MEE", haaretz:       "HAR",
  "Graham Cluley": "GC",
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

async function openUrl(url: string) {
  await fetch(`/api/open?url=${encodeURIComponent(url)}`)
}

function getCategoryColor(category: string): string {
  return CATEGORY_META[category]?.color ?? "#f0a500"
}

// ── Source badge ──────────────────────────────────────────────────────────────

function SourceBadge({ sourceId, sourceName, category }: {
  sourceId: string; sourceName: string; category: string
}) {
  const color    = getCategoryColor(category)
  const initials = SOURCE_INITIALS[sourceId] ?? sourceName.slice(0, 3).toUpperCase()
  return (
    <div className="flex items-center gap-1.5 min-w-0">
      <div
        className="flex items-center justify-center flex-shrink-0 text-[9px] font-bold"
        style={{
          width: 34, height: 20,
          background: `${color}20`,
          border:     `1px solid ${color}50`,
          color,
          fontFamily: "JetBrains Mono, monospace",
          letterSpacing: "0.05em",
        }}
      >
        {initials}
      </div>
      <span className="text-[10px] truncate"
        style={{ color: "var(--muted)", fontFamily: "JetBrains Mono, monospace" }}
      >
        {sourceName}
      </span>
    </div>
  )
}

// ── Score bar ─────────────────────────────────────────────────────────────────

function ScoreBar({ score }: { score: number }) {
  const pct   = Math.min(score / 35, 1)
  const color = pct > 0.7 ? "#ff4444" : pct > 0.4 ? "#f0a500" : "var(--accent-green)"
  return (
    <div className="flex items-center gap-1.5" title={`Score: ${score}`}>
      <div style={{ width: 36, height: 3, background: "var(--border)" }}>
        <div style={{ width: `${pct * 100}%`, height: "100%", background: color, transition: "width 0.3s" }} />
      </div>
      <span className="text-[9px]" style={{ color, fontFamily: "JetBrains Mono, monospace" }}>
        {score.toFixed(0)}
      </span>
    </div>
  )
}

// ── News card ─────────────────────────────────────────────────────────────────

function NewsCard({ item, index }: { item: NewsItem; index: number }) {
  const [imgErr, setImgErr] = useState(false)
  useEffect(() => { setImgErr(false) }, [item.id])
  const color               = getCategoryColor(item.category)
  const hasThumbnail        = item.thumbnail && !imgErr

  return (
    <div
      onClick={() => openUrl(item.url)}
      className="flex flex-col cursor-pointer transition-all duration-200 group"
      style={{
        background:     "var(--bg2)",
        border:         "1px solid var(--border)",
        borderTop:      `2px solid ${item.is_trending ? "#ff4444" : color}`,
        animation:      "fadeIn 0.2s ease both",
        animationDelay: `${Math.min(index * 12, 500)}ms`,
        breakInside:    "avoid",
        marginBottom:   "1px",
      }}
      onMouseEnter={e => {
        e.currentTarget.style.borderColor       = `${color}80`
        e.currentTarget.style.borderTopColor    = item.is_trending ? "#ff4444" : color
        e.currentTarget.style.background        = "var(--bg)"
        e.currentTarget.style.transform         = "translateY(-1px)"
      }}
      onMouseLeave={e => {
        e.currentTarget.style.borderColor       = "var(--border)"
        e.currentTarget.style.borderTopColor    = item.is_trending ? "#ff4444" : color
        e.currentTarget.style.background        = "var(--bg2)"
        e.currentTarget.style.transform         = "translateY(0)"
      }}
    >
      {/* thumbnail or stylized fallback */}
      {hasThumbnail ? (
        <div className="relative overflow-hidden flex-shrink-0" style={{ height: 200 }}>
          <img
            src={item.thumbnail}
            alt=""
            onError={() => setImgErr(true)}
            className="w-full h-full object-cover"
          />
          {/* gradient overlay */}
          <div
            className="absolute inset-0"
            style={{ background: "linear-gradient(to bottom, transparent 50%, rgba(0,0,0,0.7) 100%)" }}
          />
          {/* trending badge over image */}
          {item.is_trending && (
            <div
              className="absolute top-2 right-2 text-[9px] uppercase tracking-widest px-2 py-0.5 font-bold"
              style={{
                background: "#ff4444",
                color:      "#fff",
                fontFamily: "JetBrains Mono, monospace",
              }}
            >
              ▲ trending
            </div>
          )}
          {/* source badge over image bottom-left */}
          <div className="absolute bottom-2 left-2">
            <SourceBadge sourceId={item.source_id} sourceName={item.source_name} category={item.category} />
          </div>
        </div>
      ) : (
        <div
          className="relative flex items-center justify-center flex-shrink-0"
          style={{
            height:       200,
            background:   `linear-gradient(135deg, ${color}08 0%, ${color}18 100%)`,
            borderBottom: "1px solid var(--border)",
            overflow:     "hidden",
          }}
        >
          {/* big dim initials as texture */}
          <span
            className="absolute font-black select-none"
            style={{
              fontSize:   96,
              opacity:    0.04,
              color,
              fontFamily: "JetBrains Mono, monospace",
              lineHeight: 1,
              userSelect: "none",
            }}
          >
            {SOURCE_INITIALS[item.source_id] ?? "//"}
          </span>
          {/* source badge */}
          <div className="relative z-10 flex flex-col items-center gap-2">
            <div
              className="flex items-center justify-center font-black"
              style={{
                width:         80,
                height:        44,
                background:    `${color}20`,
                border:        `1px solid ${color}50`,
                color,
                fontFamily:    "JetBrains Mono, monospace",
                fontSize:      18,
                letterSpacing: "0.08em",
              }}
            >
              {SOURCE_INITIALS[item.source_id] ?? item.source_name.slice(0, 3).toUpperCase()}
            </div>
            <span
              className="text-[13px]"
              style={{ color: "var(--muted)", fontFamily: "JetBrains Mono, monospace" }}
            >
              {item.source_name}
            </span>
          </div>
          {/* trending badge */}
          {item.is_trending && (
            <div
              className="absolute top-2 right-2 text-[9px] uppercase tracking-widest px-2 py-0.5 font-bold"
              style={{
                background: "#ff4444",
                color:      "#fff",
                fontFamily: "JetBrains Mono, monospace",
              }}
            >
              ▲ trending
            </div>
          )}
        </div>
      )}

      {/* content */}
      <div className="flex flex-col gap-2 p-3 flex-1">

        {/* source row (only when thumbnail present, badge already shown) */}
        {hasThumbnail && (
          <div className="flex items-center justify-between gap-2">
            <SourceBadge sourceId={item.source_id} sourceName={item.source_name} category={item.category} />
            <span className="text-[9px] flex-shrink-0 uppercase tracking-widest"
              style={{ color: "var(--muted)", fontFamily: "JetBrains Mono, monospace" }}
            >
              {fmtRelative(item.published)}
            </span>
          </div>
        )}

        {/* time (when no thumbnail) */}
        {!hasThumbnail && (
          <span className="text-[9px] uppercase tracking-widest self-end"
            style={{ color: "var(--muted)", fontFamily: "JetBrains Mono, monospace" }}
          >
            {fmtRelative(item.published)}
          </span>
        )}

        {/* title */}
        <p
          className="text-[13px] font-semibold leading-snug"
          style={{
            color:           "var(--text)",
            fontFamily:      "JetBrains Mono, monospace",
            display:         "-webkit-box",
            WebkitLineClamp: 2,
            WebkitBoxOrient: "vertical",
            overflow:        "hidden",
          }}
        >
          {item.title}
        </p>

        {/* description */}
        {item.description && (
          <p
            className="text-[11px] leading-relaxed"
            style={{
              color:           "var(--muted)",
              display:         "-webkit-box",
              WebkitLineClamp: 2,
              WebkitBoxOrient: "vertical",
              overflow:        "hidden",
            }}
          >
            {item.description}
          </p>
        )}

        {/* topics */}
        {item.topics.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-0.5">
            {item.topics.slice(0, 4).map(t => {
              const tm = TOPIC_META[t]
              if (!tm) return null
              return (
                <span
                  key={t}
                  className="text-[9px] uppercase tracking-widest px-1.5 py-px"
                  style={{
                    background: `${tm.color}18`,
                    border:     `1px solid ${tm.color}40`,
                    color:      tm.color,
                    fontFamily: "JetBrains Mono, monospace",
                  }}
                >
                  {tm.label}
                </span>
              )
            })}
          </div>
        )}

        {/* footer: score bar + read arrow */}
        <div
          className="flex items-center justify-between mt-auto pt-2"
          style={{ borderTop: "1px solid var(--border)" }}
        >
          <ScoreBar score={item.score} />
          <span
            className="text-[9px] uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-opacity"
            style={{ color, fontFamily: "JetBrains Mono, monospace" }}
          >
            read →
          </span>
        </div>
      </div>
    </div>
  )
}

// ── Filter pills ──────────────────────────────────────────────────────────────

function FilterPill({ label, color, active, count, onClick }: {
  label: string; color: string; active: boolean; count: number; onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-1.5 px-2.5 py-1 text-[10px] uppercase tracking-widest transition-all duration-150 flex-shrink-0"
      style={{
        fontFamily: "JetBrains Mono, monospace",
        border:     `1px solid ${active ? color : "var(--border)"}`,
        background: active ? `${color}18` : "transparent",
        color:      active ? color : "var(--muted)",
        cursor:     "pointer",
        outline:    "none",
      }}
    >
      {label}
      {count > 0 && (
        <span style={{ opacity: 0.55, fontSize: 9 }}>{count}</span>
      )}
    </button>
  )
}

// ── Toolbar ───────────────────────────────────────────────────────────────────

function NewsToolbar({
  feed, onFeed,
  category, onCategory, topic, onTopic,
  search, onSearch, onRefresh, onClearCache,
  loading, categoryCounts, topicCounts,
}: {
  feed:           "all" | "tech" | "general"
  onFeed:         (f: "all" | "tech" | "general") => void
  category:       string
  onCategory:     (c: string) => void
  topic:          string
  onTopic:        (t: string) => void
  search:         string
  onSearch:       (s: string) => void
  onRefresh:      () => void
  onClearCache:   () => void
  loading:        boolean
  categoryCounts: Record<string, number>
  topicCounts:    Record<string, number>
}) {
  const FEED_META = {
    all:     { label: "⊕ All",              color: "#f0a500" },
    tech:    { label: "⌨ Tech & Infosec",   color: "#29b6f6" },
    general: { label: "◉ Finance & Politics", color: "#ab47bc" },
  }

  return (
    <div className="flex flex-col flex-shrink-0" style={{ borderBottom: "1px solid var(--border)" }}>

      {/* row 0: feed toggle */}
      <div className="flex flex-shrink-0" style={{ background: "var(--bg)", borderBottom: "1px solid var(--border)" }}>
        {(["all", "tech", "general"] as const).map(f => {
          const meta   = FEED_META[f]
          const active = feed === f
          return (
            <button
              key={f}
              onClick={() => onFeed(f)}
              className="flex-1 py-2 text-[10px] uppercase tracking-widest transition-all duration-150"
              style={{
                fontFamily:   "JetBrains Mono, monospace",
                background:   active ? `${meta.color}15` : "transparent",
                color:        active ? meta.color : "var(--muted)",
                border:       "none",
                borderBottom: active ? `2px solid ${meta.color}` : "2px solid transparent",
                cursor:       "pointer",
              }}
            >
              {meta.label}
            </button>
          )
        })}
      </div>

      {/* row 1: actions + optional category pills */}
      <div
        className="flex items-center gap-1.5 px-4 py-2 overflow-x-auto"
        style={{ background: "var(--bg2)", scrollbarWidth: "none" }}
      >
        {/* category pills — only when a specific feed is selected */}
        {feed !== "all" && Object.entries(CATEGORY_META)
          .filter(([id]) => {
            if (feed === "tech")    return ["infosec", "tech", "government"].includes(id)
            if (feed === "general") return ["finance", "politics", "mainstream"].includes(id)
            return false
          })
          .map(([id, { label, color }]) => (
            <FilterPill
              key={id} label={label} color={color}
              active={category === id}
              count={categoryCounts[id] ?? 0}
              onClick={() => onCategory(id)}
            />
          ))}

        <div className={`flex items-center gap-2 flex-shrink-0 ${feed !== "all" ? "ml-auto pl-3" : ""}`}
          style={feed !== "all" ? { borderLeft: "1px solid var(--border)" } : {}}
        >
          <button onClick={onRefresh} disabled={loading}
            className="text-[10px] uppercase tracking-widest px-3 py-1 transition-all"
            style={{
              fontFamily: "JetBrains Mono, monospace",
              border:     "1px solid var(--border)",
              color:      loading ? "var(--muted)" : "var(--accent-green)",
              background: "transparent",
              cursor:     loading ? "default" : "pointer",
              opacity:    loading ? 0.5 : 1,
            }}
          >
            {loading ? "···" : "⟳ refresh"}
          </button>
          <button onClick={onClearCache}
            className="text-[10px] uppercase tracking-widest px-3 py-1 transition-all"
            style={{
              fontFamily: "JetBrains Mono, monospace",
              border:     "1px solid var(--border)",
              color:      "var(--muted)",
              background: "transparent",
              cursor:     "pointer",
            }}
            onMouseEnter={e => { e.currentTarget.style.color = "#ff4444"; e.currentTarget.style.borderColor = "#ff4444" }}
            onMouseLeave={e => { e.currentTarget.style.color = "var(--muted)"; e.currentTarget.style.borderColor = "var(--border)" }}
          >
            ✕ cache
          </button>
        </div>
      </div>

      {/* row 2: topic pills — only when a category is selected */}
      {category !== "all" && (
        <div
          className="flex items-center gap-1 px-4 py-1.5 overflow-x-auto"
          style={{ background: "var(--bg)", borderTop: "1px solid var(--border)", scrollbarWidth: "none" }}
        >
          {(CATEGORY_TOPICS[category] ?? []).map(id => {
            const tm = TOPIC_META[id]
            if (!tm) return null
            return (
              <FilterPill
                key={id} label={tm.label} color={tm.color}
                active={topic === id}
                count={topicCounts[id] ?? 0}
                onClick={() => onTopic(topic === id ? "all" : id)}
              />
            )
          })}
        </div>
      )}

      {/* row 2: search */}
      <div
        className="flex items-center gap-3 px-4 py-2"
        style={{ background: "var(--bg2)", borderTop: "1px solid var(--border)" }}
      >
        <span className="text-[11px]" style={{ color: "var(--muted)" }}>⌕</span>
        <input
          type="text"
          value={search}
          onChange={e => onSearch(e.target.value)}
          placeholder="search headlines, sources, keywords..."
          className="flex-1 bg-transparent text-[11px] outline-none"
          style={{
            color:      "var(--text)",
            fontFamily: "JetBrains Mono, monospace",
            border:     "none",
            caretColor: "#f0a500",
          }}
        />
        {search && (
          <button onClick={() => onSearch("")}
            style={{ color: "var(--muted)", background: "none", border: "none", cursor: "pointer", fontSize: 11 }}
          >✕</button>
        )}
        <span className="text-[10px] flex-shrink-0"
          style={{ color: "var(--muted)", fontFamily: "JetBrains Mono, monospace" }}
        >
          {categoryCounts["_filtered"] ?? 0} articles
        </span>
      </div>
    </div>
  )
}

// ── Main export ───────────────────────────────────────────────────────────────

export default function NewsPanel() {
  const [items,    setItems]    = useState<NewsItem[]>([])
  const [loading,  setLoading]  = useState(true)
  const [error,    setError]    = useState<string | null>(null)
  const [feed,     setFeed]     = useState<"all" | "tech" | "general">("all")
  const [category, setCategory] = useState("all")
  const [topic,    setTopic]    = useState("all")
  const [search,   setSearch]   = useState("")

  const fetchNews = async (currentFeed = feed) => {
    setLoading(true)
    setError(null)
    try {
      const endpoint = currentFeed === "tech"    ? "/api/news/tech"
                     : currentFeed === "general" ? "/api/news/general"
                     : "/api/news"
      const r = await fetch(endpoint)
      const d = await r.json()
      if (d.error) setError(d.error)
      else setItems(d.items ?? [])
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const clearCache = async () => {
    const endpoint = feed === "tech"    ? "/api/news/tech/cache"
                   : feed === "general" ? "/api/news/general/cache"
                   : "/api/news/cache"
    await fetch(endpoint, { method: "DELETE" })
    fetchNews()
  }

  const handleFeed = (f: "all" | "tech" | "general") => {
    setFeed(f)
    setCategory("all")
    setTopic("all")
    setSearch("")
    fetchNews(f)
  }

  const handleCategory = (c: string) => {
    const next = category === c ? "all" : c
    setCategory(next)
    setTopic("all")
    setSearch("")
    setItems([])
    fetchNews(feed)
  }

  const handleTopic = (t: string) => {
    setTopic(prev => prev === t ? "all" : t)
    setItems([])
    fetchNews(feed)
  }

  useEffect(() => { fetchNews() }, [])

  const categoryCounts = useMemo(() => {
    const c: Record<string, number> = { all: items.length }
    for (const item of items) {
      c[item.category] = (c[item.category] ?? 0) + 1
    }
    return c
  }, [items])

  const topicCounts = useMemo(() => {
    const base = category === "all" ? items : items.filter(i => i.category === category)
    const c: Record<string, number> = {}
    for (const item of base) {
      for (const t of item.topics) {
        c[t] = (c[t] ?? 0) + 1
      }
    }
    return c
  }, [items, category])

  const filtered = useMemo(() => {
    let list = [...items]
    if (category !== "all") list = list.filter(i => i.category === category)
    if (topic !== "all")    list = list.filter(i => i.topics.includes(topic))
    if (search.trim()) {
      const q = search.toLowerCase()
      list = list.filter(i =>
        [i.title, i.description, i.source_name, ...i.keywords, ...i.topics]
          .join(" ").toLowerCase().includes(q)
      )
    }
    return list
  }, [items, category, topic, search])

  const countsWithFiltered = useMemo(() => ({
    ...categoryCounts,
    _filtered: filtered.length,
  }), [categoryCounts, filtered.length])

  return (
    <div className="flex-1 flex flex-col min-h-0 overflow-hidden w-full">

      <NewsToolbar
        feed={feed}       onFeed={handleFeed}
        category={category}
        onCategory={handleCategory}
        topic={topic}
        onTopic={handleTopic}
        search={search}       onSearch={setSearch}
        onRefresh={fetchNews} onClearCache={clearCache}
        loading={loading}
        categoryCounts={countsWithFiltered}
        topicCounts={topicCounts}
      />

      <div className="flex-1 overflow-y-auto min-h-0 p-2">

        {loading && (
          <div className="flex items-center justify-center py-32 gap-3">
            <span className="inline-block w-5 h-5 rounded-full border-2 animate-spin"
              style={{ borderColor: "var(--border)", borderTopColor: "#f0a500" }}
            />
            <p className="text-xs uppercase tracking-widest"
              style={{ color: "var(--muted)", fontFamily: "JetBrains Mono, monospace" }}
            >
              Fetching intelligence feeds...
            </p>
          </div>
        )}

        {!loading && error && (
          <div className="flex flex-col items-center justify-center py-32 gap-3">
            <span className="text-4xl opacity-20">⚠</span>
            <p className="text-xs" style={{ color: "#ff4444" }}>{error}</p>
          </div>
        )}

        {!loading && !error && filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center py-32 gap-3">
            <span className="text-4xl opacity-20">📡</span>
            <p className="text-xs uppercase tracking-widest"
              style={{ color: "var(--muted)", fontFamily: "JetBrains Mono, monospace" }}
            >
              No articles found.
            </p>
          </div>
        )}

        {!loading && !error && filtered.length > 0 && (
          <div style={{
            display:             "grid",
            gridTemplateColumns: "1fr 1fr",
            gap:                 "1px",
            alignItems:          "start",
          }}>
            {filtered.map((item, idx) => (
              <NewsCard key={`${item.id}-${item.source_id}`} item={item} index={idx} />
            ))}
          </div>
        )}
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  )
}

