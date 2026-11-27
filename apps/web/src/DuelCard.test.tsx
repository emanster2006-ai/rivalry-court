import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import type { Duel, Person } from './client'
import { DuelCard } from './DuelCard'

afterEach(cleanup)

const a: Person = { id: 'a', username: 'captain_e', display_name: 'captain_e', role: 'member' }
const b: Person = { id: 'b', username: 'rival_1', display_name: 'rival_1', role: 'member' }
const members = [a, b]

function duel(overrides: Partial<Duel>): Duel {
  return {
    id: 'duel', group_id: 'group', gameweek: 'GW8', claim_type: 'gameweek_points',
    member_a_id: 'a', member_b_id: 'b', deadline_at: new Date(Date.now() - 60000).toISOString(),
    status: 'awaiting_scores', probabilities: { a: 60, b: 45 }, scores: [], void_reason: null,
    ...overrides,
  }
}

const revision = { id: 'rev', score_a: 70, score_b: 62, source_url: 'https://fantasy.premierleague.com/',
  created_at: new Date().toISOString(), entered_by: 'a', responses: [] as never[] }

function renderCard(d: Duel, me: Person, admin: boolean) {
  const act = vi.fn()
  render(<DuelCard duel={d} me={me} members={members} admin={admin} busy={false} act={act} />)
  return act
}

test('after the deadline both probabilities are shown and nobody can revise', () => {
  renderCard(duel({}), a, false)
  expect(screen.getByText(/captain_e: 60%/)).toBeTruthy()
  expect(screen.getByText(/rival_1: 45%/)).toBeTruthy()
  expect(screen.queryByRole('slider')).toBeNull()
})

test('only an admin sees score entry, and it posts both values with the source', () => {
  const act = renderCard(duel({}), a, true)
  fireEvent.click(screen.getByText('Enter final score'))
  fireEvent.change(screen.getByLabelText('captain_e points'), { target: { value: '70' } })
  fireEvent.change(screen.getByLabelText('rival_1 points'), { target: { value: '62' } })
  fireEvent.change(screen.getByLabelText('Official FPL source URL'), { target: { value: 'https://fantasy.premierleague.com/x' } })
  fireEvent.click(screen.getByText(/Post score/))
  expect(act).toHaveBeenCalledWith('/duels/duel/scores', { score_a: 70, score_b: 62, source_url: 'https://fantasy.premierleague.com/x' })
})

test('a non-admin does not get score entry', () => {
  renderCard(duel({}), b, false)
  expect(screen.queryByText('Enter final score')).toBeNull()
})

test('a participant can confirm the latest score', () => {
  const act = renderCard(duel({ status: 'awaiting_confirmation', scores: [revision] }), b, false)
  expect(screen.getByText('70–62')).toBeTruthy()
  expect(screen.queryByText('captain_e won')).toBeNull()
  fireEvent.click(screen.getByText('Confirm score'))
  expect(act).toHaveBeenCalledWith('/duels/duel/scores/rev/confirm')
})

test('a participant can dispute with a reason', () => {
  const act = renderCard(duel({ status: 'awaiting_confirmation', scores: [revision] }), b, false)
  fireEvent.change(screen.getByLabelText('Dispute with reason'), { target: { value: 'My captain scored more points' } })
  fireEvent.click(screen.getByText('Dispute'))
  expect(act).toHaveBeenCalledWith('/duels/duel/scores/rev/dispute', { reason: 'My captain scored more points' })
})

test('someone who already responded cannot respond again', () => {
  const answered = { ...revision, responses: [{ user_id: 'b', action: 'confirm' as const, reason: null, created_at: revision.created_at }] }
  renderCard(duel({ status: 'awaiting_confirmation', scores: [answered] }), b, false)
  expect(screen.queryByText('Confirm score')).toBeNull()
})

test('the admin can void an open duel', () => {
  const open = duel({ status: 'open', deadline_at: new Date(Date.now() + 600000).toISOString(), probabilities: {} })
  const act = renderCard(open, a, true)
  fireEvent.click(screen.getByText('Wrong deadline?'))
  fireEvent.change(screen.getByLabelText('Reason'), { target: { value: 'Deadline was moved' } })
  fireEvent.click(screen.getByText('Void duel'))
  expect(act).toHaveBeenCalledWith('/duels/duel/void', { reason: 'Deadline was moved' })
})

test('the slider starts at the saved probability and updates after a revision', () => {
  const open = duel({ status: 'open', deadline_at: new Date(Date.now() + 600000).toISOString(), probabilities: { a: 70 } })
  const act = vi.fn()
  const { rerender } = render(<DuelCard duel={open} me={a} members={members} admin={false} busy={false} act={act} />)
  const slider = screen.getByRole('slider') as HTMLInputElement
  expect(slider.value).toBe('70')
  fireEvent.change(slider, { target: { value: '85' } })
  rerender(<DuelCard duel={{ ...open, probabilities: { a: 70 } }} me={a} members={members} admin={false} busy={false} act={act} />)
  expect(slider.value).toBe('85')
  rerender(<DuelCard duel={{ ...open, probabilities: { a: 80 } }} me={a} members={members} admin={false} busy={false} act={act} />)
  expect(slider.value).toBe('80')
})

test('a resolved result shows the winner, score, both predictions and source', () => {
  renderCard(duel({ status: 'resolved', scores: [revision] }), a, false)
  expect(screen.getByText('You won')).toBeTruthy()
  expect(screen.getByText('70–62')).toBeTruthy()
  expect(screen.getByText('You gave yourself a 60% chance of winning.')).toBeTruthy()
  expect(screen.getByText('rival_1: 45%')).toBeTruthy()
  expect(screen.getByRole('link', { name: 'Official FPL score' }).getAttribute('href')).toBe(revision.source_url)
})

test('a result can be shared using its existing group-protected duel link', async () => {
  const writeText = vi.fn().mockResolvedValue(undefined)
  const clipboard = vi.spyOn(window, 'navigator', 'get').mockReturnValue({ clipboard: { writeText } } as unknown as Navigator)
  try {
    renderCard(duel({ status: 'resolved', scores: [revision] }), a, false)
    fireEvent.click(screen.getByRole('button', { name: 'Copy result link' }))
    expect(writeText).toHaveBeenCalledWith(`${window.location.origin}/?duel=duel`)
    await screen.findByText('Link copied. Group members can open it.')
  } finally {
    clipboard.mockRestore()
  }
})

test('a rematch keeps the participants and claim but asks for a new gameweek and deadline', async () => {
  const onRematch = vi.fn().mockResolvedValue(true)
  render(<DuelCard duel={duel({ claim_type: 'captain_points', status: 'resolved', scores: [revision] })}
    me={a} members={members} admin busy={false} act={vi.fn()} onRematch={onRematch} />)
  fireEvent.click(screen.getByRole('button', { name: 'Set up rematch' }))
  const deadline = '2026-12-09T18:30'
  expect((screen.getByLabelText('FPL deadline') as HTMLInputElement).value).toBe('')
  expect(screen.queryByLabelText('Side A')).toBeNull()
  fireEvent.change(screen.getByLabelText('Gameweek'), { target: { value: 'GW9' } })
  fireEvent.change(screen.getByLabelText('FPL deadline'), { target: { value: deadline } })
  fireEvent.click(screen.getByRole('button', { name: 'Create rematch' }))
  expect(onRematch).toHaveBeenCalledWith({
    member_a_id: 'a', member_b_id: 'b', claim_type: 'captain_points', gameweek: 'GW9',
    deadline_at: new Date(deadline).toISOString(),
  })
  await waitFor(() => expect(screen.queryByLabelText('FPL deadline')).toBeNull())
})
