import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, expect, test, vi } from 'vitest'
import App from './App'
import { api, auth } from './client'

vi.mock('./client', () => ({
  auth: {
    getSession: vi.fn(), onAuthStateChange: vi.fn(() => ({ data: { subscription: { unsubscribe() {} } } })),
    signInWithOtp: vi.fn(), signOut: vi.fn(),
  },
  api: vi.fn(),
}))

beforeEach(() => { cleanup(); vi.clearAllMocks() })

test('email sign-in uses a magic link', async () => {
  vi.mocked(auth.getSession).mockResolvedValue({ data: { session: null }, error: null })
  vi.mocked(auth.signInWithOtp).mockResolvedValue({ data: { user: null, session: null }, error: null })
  render(<App />)
  fireEvent.change(screen.getByPlaceholderText('you@example.com'), { target: { value: 'friend@example.com' } })
  fireEvent.click(screen.getByText('Send sign-in link'))
  await waitFor(() => expect(auth.signInWithOtp).toHaveBeenCalledWith({ email: 'friend@example.com', options: { emailRedirectTo: window.location.origin } }))
})

test('a participant can see and revise only their own pre-deadline probability', async () => {
  vi.mocked(auth.getSession).mockResolvedValue({ data: { session: { access_token: 'test' } }, error: null } as never)
  const duel = { id: 'duel', group_id: 'group', gameweek: 'GW8', claim_type: 'gameweek_points',
    member_a_id: 'a', member_b_id: 'b', deadline_at: new Date(Date.now() + 600000).toISOString(),
    status: 'open', probabilities: { a: 60 }, scores: [], void_reason: null }
  vi.mocked(api).mockImplementation(async (path: string) => {
    if (path === '/me') return { id: 'a', email: 'a@example.com' }
    if (path === '/groups') return [{ id: 'group', name: 'Friends', role: 'member' }]
    if (path.endsWith('/members')) return [{ id: 'a', email: 'a@example.com', role: 'member' }, { id: 'b', email: 'b@example.com', role: 'member' }]
    if (path.endsWith('/duels')) return [duel]
    if (path.endsWith('/history')) return {}
    return {}
  })
  render(<App />)
  await waitFor(() => expect(screen.getByText(/a@example.com: 60%/)).toBeTruthy())
  expect(screen.getByText(/b@example.com: Sealed/)).toBeTruthy()
  fireEvent.change(screen.getByLabelText('Your win probability'), { target: { value: '75' } })
  fireEvent.click(screen.getByText('Lock / revise'))
  await waitFor(() => expect(api).toHaveBeenCalledWith('/duels/duel/submissions', 'POST', { probability_pct: 75 }))
})

test('a signed-in member can retry after a temporary API failure', async () => {
  vi.mocked(auth.getSession).mockResolvedValue({ data: { session: { access_token: 'test' } }, error: null } as never)
  let failing = true
  vi.mocked(api).mockImplementation(async (path: string) => {
    if (path === '/me') {
      if (failing) throw new TypeError('Failed to fetch')
      return { id: 'a', email: 'a@example.com' }
    }
    if (path === '/groups') return []
    return {}
  })
  render(<App />)
  await waitFor(() => expect(screen.getByRole('alert').textContent).toContain('Failed to fetch'))
  failing = false
  fireEvent.click(screen.getByText('Try again'))
  await waitFor(() => expect(screen.queryByRole('alert')).toBeNull())
  expect(screen.getByText('a@example.com')).toBeTruthy()
})
