// frontend/src/shared/types.ts

export interface FeedItem {
  platform: 'youtube' | 'x' | 'telegram' | 'reddit'
  id: string
  title: string
  author: string
  avatar: string
  thumbnail: string
  url: string
  published: string
  description: string
  channel_id?: string
  quote_img?:    string
  quote_author?: string
}

export interface PlatformMeta {
  error: string | null
  from_cache: boolean | null
}

export interface FeedResponse {
  items: FeedItem[]
  meta: {
    youtube:  PlatformMeta
    x:        PlatformMeta
    telegram: PlatformMeta
  }
}

export interface StatusResponse {
  youtube: {
    authenticated:     boolean
    has_client_secret: boolean
  }
  x: {
    has_following_file: boolean
    handle_count:       number
  }
}

export type SortOption = 'date_desc' | 'date_asc' | 'author'

export interface FeedFilters {
  search: string
  sort:   SortOption
}

