import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import type { Duel, Person } from './client'

function label(type: string) { return type === 'captain_points' ? 'Captain slot points' : 'Gameweek points after transfer penalties' }
function date(value: string) { return new Date(value).toLocaleString() }

export function CreateDuelForm({ members, busy, onCreate }: { members: Person[]; busy: boolean; onCreate: (body: unknown) => void }) {
  const [a, setA] = useState(''); const [b, setB] = useState(''); const [type, setType] = useState('gameweek_points')
  const [gameweek, setGameweek] = useState(''); const [deadline, setDeadline] = useState('')
  useEffect(() => {
    const has = (id: string) => members.some(m => m.id === id)
    setA(current => has(current) ? current : members[0]?.id || '')
    setB(current => has(current) ? current : members[1]?.id || '')
  }, [members])
  return <form className="panel create-duel" onSubmit={event => { event.preventDefault(); onCreate({ member_a_id: a, member_b_id: b, claim_type: type, gameweek, deadline_at: new Date(deadline).toISOString() }) }}>
    <div><p className="eyebrow">ADMIN</p><h3>New duel</h3><p>Enter the official FPL deadline in your local time. It locks once a prediction is submitted.</p></div>
    <div className="form-grid"><label>Side A<select value={a} onChange={event => setA(event.target.value)} required>{members.map(m => <option value={m.id} key={m.id}>{m.email}</option>)}</select></label>
      <label>Side B<select value={b} onChange={event => setB(event.target.value)} required>{members.map(m => <option value={m.id} key={m.id}>{m.email}</option>)}</select></label>
      <label>Claim<select value={type} onChange={event => setType(event.target.value)}><option value="gameweek_points">Gameweek points</option><option value="captain_points">Captain slot points</option></select></label>
      <label>Gameweek<input value={gameweek} onChange={event => setGameweek(event.target.value)} placeholder="2026/27 GW8" required /></label>
      <label>FPL deadline<input type="datetime-local" value={deadline} onChange={event => setDeadline(event.target.value)} required /></label>
      <button disabled={busy || members.length < 2 || a === b}>Create duel</button></div>
  </form>
}

export function DuelCard({ duel, me, members, admin, busy, act }: { duel: Duel; me: Person; members: Person[]; admin: boolean; busy: boolean; act: (path: string, body?: unknown) => void }) {
  const [probability, setProbability] = useState(50)
  const [scoreA, setScoreA] = useState(''); const [scoreB, setScoreB] = useState(''); const [source, setSource] = useState('')
  const [reason, setReason] = useState(''); const [voidReason, setVoidReason] = useState('')
  const a = members.find(m => m.id === duel.member_a_id)?.email || 'Side A'
  const b = members.find(m => m.id === duel.member_b_id)?.email || 'Side B'
  const latest = duel.scores.at(-1)
  const participant = [duel.member_a_id, duel.member_b_id].includes(me.id)
  const responded = latest?.responses.some(response => response.user_id === me.id)
  const open = duel.status === 'open' && new Date() < new Date(duel.deadline_at)
  const canScore = admin && ['awaiting_scores', 'disputed', 'awaiting_confirmation', 'resolved'].includes(duel.status)
  const canRespond = participant && latest && !responded && ['awaiting_confirmation', 'disputed'].includes(duel.status)
  function submit(event: FormEvent, path: string, body: unknown) { event.preventDefault(); act(path, body) }
  return <article className="panel duel"><div className="duel-top"><span className="badge">{duel.gameweek}</span><span className={`status ${duel.status}`}>{duel.status.replaceAll('_', ' ')}</span></div>
    <h3>{a} <em>vs</em> {b}</h3><p>{label(duel.claim_type)}</p><p className="muted">Locks {date(duel.deadline_at)}</p>
    <div className="predictions"><span>{a}: {duel.probabilities[duel.member_a_id] === undefined ? 'Sealed' : `${duel.probabilities[duel.member_a_id]}%`}</span><span>{b}: {duel.probabilities[duel.member_b_id] === undefined ? 'Sealed' : `${duel.probabilities[duel.member_b_id]}%`}</span></div>
    {open && participant && <form className="inline-form" onSubmit={event => submit(event, `/duels/${duel.id}/submissions`, { probability_pct: probability })}>
      <label>Your chance of winning <strong>{probability}%</strong><input aria-label="Your win probability" type="range" min="0" max="100" step="5" value={probability} onChange={event => setProbability(Number(event.target.value))} /></label>
      <button disabled={busy}>Lock / revise</button></form>}
    {duel.void_reason && <p className="muted">{duel.void_reason}</p>}
    {duel.scores.length > 0 && <details open={duel.status === 'disputed'}><summary>Score record ({duel.scores.length})</summary><ol>{duel.scores.map((revision, index) => <li key={revision.id}>
      <strong>Entry {index + 1}: {revision.score_a}–{revision.score_b}</strong> · <a href={revision.source_url} target="_blank" rel="noreferrer">FPL source</a> · {date(revision.created_at)}
      {revision.responses.map(response => <p key={response.user_id} className="muted">{members.find(m => m.id === response.user_id)?.email}: {response.action}{response.reason ? ` — ${response.reason}` : ''}</p>)}
    </li>)}</ol></details>}
    {canRespond && <div className="review"><button disabled={busy} onClick={() => act(`/duels/${duel.id}/scores/${latest.id}/confirm`)}>Confirm score</button>
      <form onSubmit={event => submit(event, `/duels/${duel.id}/scores/${latest.id}/dispute`, { reason })}><label>Dispute with reason<input minLength={10} maxLength={1000} value={reason} onChange={event => setReason(event.target.value)} placeholder="Explain what is wrong" required /></label><button className="secondary" disabled={busy}>Dispute</button></form></div>}
    {canScore && <details><summary>{latest ? 'Correct or reaffirm score' : 'Enter final score'}</summary><form className="form-grid score-form" onSubmit={event => submit(event, `/duels/${duel.id}/scores`, { score_a: Number(scoreA), score_b: Number(scoreB), source_url: source })}>
      <p className="full muted">Wait until FPL finalizes this gameweek, including postponed fixtures. Enter official captain slot points for captain duels.</p>
      <label>{a} points<input type="number" min="0" value={scoreA} onChange={event => setScoreA(event.target.value)} required /></label><label>{b} points<input type="number" min="0" value={scoreB} onChange={event => setScoreB(event.target.value)} required /></label>
      <label className="full">Official FPL source URL<input type="url" value={source} onChange={event => setSource(event.target.value)} placeholder="https://fantasy.premierleague.com/..." required /></label><button disabled={busy}>Post score &amp; email players</button></form></details>}
    {admin && duel.status === 'open' && <details><summary>Wrong deadline?</summary><form className="inline-form" onSubmit={event => submit(event, `/duels/${duel.id}/void`, { reason: voidReason })}><label>Reason<input minLength={5} value={voidReason} onChange={event => setVoidReason(event.target.value)} required /></label><button className="secondary" disabled={busy}>Void duel</button></form></details>}
  </article>
}
