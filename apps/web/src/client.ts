import { AuthClient } from '@supabase/auth-js'

export const auth = new AuthClient({ url: import.meta.env.VITE_AUTH_URL || 'http://localhost:9999' })
const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8001'

export async function api<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const { data: { session } } = await auth.getSession()
  if (!session) throw new Error('Please sign in again')
  const response = await fetch(`${apiUrl}${path}`, {
    method,
    headers: { Authorization: `Bearer ${session.access_token}`, 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({})) as { detail?: string | { msg: string }[] }
    const detail = Array.isArray(error.detail) ? error.detail.map(item => item.msg).join(', ') : error.detail
    throw new Error(detail || `Request failed (${response.status})`)
  }
  return response.json() as Promise<T>
}

export interface Person { id: string; email: string; role: string }
export interface Group { id: string; name: string; role: string; invite_code?: string }
export interface ScoreResponse { user_id: string; action: 'confirm' | 'dispute'; reason: string | null; created_at: string }
export interface ScoreRevision { id: string; score_a: number; score_b: number; source_url: string; created_at: string; entered_by: string; responses: ScoreResponse[] }
export interface Duel {
  id: string; group_id: string; gameweek: string; claim_type: 'gameweek_points' | 'captain_points';
  member_a_id: string; member_b_id: string; deadline_at: string; status: string;
  probabilities: Record<string, number>; scores: ScoreRevision[]; void_reason: string | null
}
export interface HistoryEntry { duel_id: string; gameweek: string; claim_type: string; status: string; void_reason: string | null; probability_pct?: number; won?: boolean; brier?: number }
export interface MemberHistory { email: string; sample_size: number; mean_brier: number | null; wins: number; losses: number; history: HistoryEntry[] }
