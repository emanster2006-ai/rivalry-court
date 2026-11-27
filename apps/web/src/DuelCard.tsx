import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import type { Duel, Person } from './client'

function label(type: string) { return type === 'captain_points' ? 'Captain slot points' : 'Gameweek points after transfer penalties' }
function date(value: string) { return new Date(value).toLocaleString() }
function deadlineLabel(value: string) {
  return new Date(value).toLocaleString(undefined, {
    weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', timeZoneName: 'short',
  })
}

type Matchup = Pick<Duel, 'member_a_id' | 'member_b_id' | 'claim_type'>
export type CreateDuelInput = Matchup & Pick<Duel, 'gameweek' | 'deadline_at'>

export function duelAction(duel: Duel, userId: string, admin: boolean, now: number) {
  const participant = duel.member_a_id === userId || duel.member_b_id === userId
  if (participant && duel.status === 'open' && Date.parse(duel.deadline_at) > now) {
    return duel.probabilities[userId] === undefined ? 'predict' : 'saved'
  }
  const latest = duel.scores.at(-1)
  if (participant && latest && ['awaiting_confirmation', 'disputed'].includes(duel.status)
      && !latest.responses.some(response => response.user_id === userId)) return 'review'
  if (admin && duel.status === 'awaiting_scores') return 'score'
}

export function CreateDuelForm({ members, busy, onCreate, rematch }: {
  members: Person[]; busy: boolean; onCreate: (body: CreateDuelInput) => void; rematch?: Matchup
}) {
  const [a, setA] = useState(''); const [b, setB] = useState(''); const [type, setType] = useState<Duel['claim_type']>('gameweek_points')
  const [gameweek, setGameweek] = useState(''); const [deadline, setDeadline] = useState('')
  useEffect(() => {
    const has = (id: string) => members.some(m => m.id === id)
    setA(current => has(current) ? current : members[0]?.id || '')
    setB(current => has(current) ? current : members[1]?.id || '')
  }, [members])
  const matchup = rematch ?? { member_a_id: a, member_b_id: b, claim_type: type }
  return <form className={rematch ? 'rematch-form' : 'panel create-duel'} onSubmit={event => {
    event.preventDefault()
    onCreate({ ...matchup, gameweek, deadline_at: new Date(deadline).toISOString() })
  }}>
    <div><h3>{rematch ? 'Set the next gameweek' : 'New duel'}</h3><p>Enter the official FPL deadline in your local time.</p></div>
    <div className="form-grid">{!rematch && <><label>Side A<select value={a} onChange={event => setA(event.target.value)} required>{members.map(m => <option value={m.id} key={m.id}>{m.display_name}</option>)}</select></label>
      <label>Side B<select value={b} onChange={event => setB(event.target.value)} required>{members.map(m => <option value={m.id} key={m.id}>{m.display_name}</option>)}</select></label>
      <label>Claim<select value={type} onChange={event => setType(event.target.value as Duel['claim_type'])}><option value="gameweek_points">Gameweek points</option><option value="captain_points">Captain slot points</option></select></label></>}
      <label>Gameweek<input value={gameweek} onChange={event => setGameweek(event.target.value)} placeholder="2026/27 GW8" required /></label>
      <label>FPL deadline<input type="datetime-local" value={deadline} onChange={event => setDeadline(event.target.value)} required /></label>
      <button disabled={busy || !matchup.member_a_id || !matchup.member_b_id || matchup.member_a_id === matchup.member_b_id}>
        {rematch ? 'Create rematch' : 'Create duel'}
      </button></div>
  </form>
}

export function DuelCard({ duel, me, members, admin, busy, act, featured, onRematch }: {
  duel: Duel; me: Person; members: Person[]; admin: boolean; busy: boolean
  act: (path: string, body?: unknown) => void; featured?: boolean
  onRematch?: (body: CreateDuelInput) => Promise<boolean>
}) {
  const [rematchOpen, setRematchOpen] = useState(false)
  const [copyStatus, setCopyStatus] = useState<'copied' | 'manual'>()
  const savedProbability = duel.probabilities[me.id]
  const [probability, setProbability] = useState(savedProbability ?? 50)
  useEffect(() => setProbability(savedProbability ?? 50), [me.id, savedProbability])
  const [scoreA, setScoreA] = useState(''); const [scoreB, setScoreB] = useState(''); const [source, setSource] = useState('')
  const [reason, setReason] = useState(''); const [voidReason, setVoidReason] = useState('')
  const a = members.find(m => m.id === duel.member_a_id)?.display_name || 'Side A'
  const b = members.find(m => m.id === duel.member_b_id)?.display_name || 'Side B'
  const latest = duel.scores.at(-1)
  const participant = [duel.member_a_id, duel.member_b_id].includes(me.id)
  const action = duelAction(duel, me.id, admin, Date.now())
  const canPredict = action === 'predict' || action === 'saved'
  const canScore = admin && ['awaiting_scores', 'disputed', 'awaiting_confirmation', 'resolved'].includes(duel.status)
  const winnerId = latest && duel.status === 'resolved'
    ? (latest.score_a > latest.score_b ? duel.member_a_id : duel.member_b_id)
    : undefined
  const winner = winnerId === duel.member_a_id ? a : b
  const resultUrl = `${window.location.origin}/?duel=${encodeURIComponent(duel.id)}`
  const actionLabel = { predict: 'Make your pick', saved: 'Prediction saved', review: 'Review your result', score: 'Post the final score' }
  function submit(event: FormEvent, path: string, body: unknown) { event.preventDefault(); act(path, body) }

  async function copyResultLink() {
    try {
      await navigator.clipboard.writeText(resultUrl)
      setCopyStatus('copied')
    } catch {
      setCopyStatus('manual')
    }
  }

  return <article className={`panel duel${featured ? ' featured-duel' : ''}`}>
    <div className="duel-top"><span className="badge">{duel.gameweek}</span><span className={`status ${duel.status}`}>{duel.status.replaceAll('_', ' ')}</span></div>
    {featured && action && <h3 className="duel-action">{actionLabel[action]}</h3>}
    {featured && action ? <p className="matchup">{a} <em>vs</em> {b}</p> : <h3>{a} <em>vs</em> {b}</h3>}
    <p>{label(duel.claim_type)}</p>
    {duel.status === 'open' && <p className="muted">Deadline <time dateTime={duel.deadline_at}>{deadlineLabel(duel.deadline_at)}</time></p>}
    {latest && <div className="duel-result">
      {winnerId && <p className="result-title">{winnerId === me.id ? 'You won' : `${winner} won`}</p>}
      <p className="result-score">{a} <strong>{latest.score_a}–{latest.score_b}</strong> {b}</p>
      {winnerId && participant && savedProbability !== undefined && <p>You gave yourself a {savedProbability}% chance of winning.</p>}
      <a href={latest.source_url} target="_blank" rel="noreferrer">Official FPL score</a>
    </div>}
    <div className="predictions"><span>{a}: {duel.probabilities[duel.member_a_id] === undefined ? (duel.status === 'open' ? 'Sealed' : 'No revealed pick') : `${duel.probabilities[duel.member_a_id]}%`}</span><span>{b}: {duel.probabilities[duel.member_b_id] === undefined ? (duel.status === 'open' ? 'Sealed' : 'No revealed pick') : `${duel.probabilities[duel.member_b_id]}%`}</span></div>
    {winnerId && <div className="share-result">
      <button type="button" className="secondary" onClick={copyResultLink}>Copy result link</button>
      {copyStatus === 'copied' && <p className="muted" role="status">Link copied. Group members can open it.</p>}
      {copyStatus === 'manual' && <label>Result link<input value={resultUrl} readOnly onFocus={event => event.currentTarget.select()} /></label>}
    </div>}
    {action === 'saved' && <p className="muted" role="status">{savedProbability}% saved · editable until the deadline</p>}
    {canPredict && <form className="inline-form" onSubmit={event => submit(event, `/duels/${duel.id}/submissions`, { probability_pct: probability })}>
      <label>Your chance of winning <strong>{probability}%</strong><input aria-label="Your win probability" type="range" min="0" max="100" step="5" value={probability} onChange={event => setProbability(Number(event.target.value))} /></label>
      <button disabled={busy}>{action === 'saved' ? 'Update prediction' : 'Save prediction'}</button></form>}
    {duel.void_reason && <p className="muted">{duel.void_reason}</p>}
    {duel.scores.length > 0 && <details open={duel.status === 'disputed'}><summary>Score record ({duel.scores.length})</summary><ol>{duel.scores.map((revision, index) => <li key={revision.id}>
      <strong>Entry {index + 1}: {revision.score_a}–{revision.score_b}</strong> · <a href={revision.source_url} target="_blank" rel="noreferrer">FPL source</a> · {date(revision.created_at)}
      {revision.responses.map(response => <p key={response.user_id} className="muted">{members.find(m => m.id === response.user_id)?.display_name}: {response.action}{response.reason ? ` — ${response.reason}` : ''}</p>)}
    </li>)}</ol></details>}
    {action === 'review' && latest && <div className="review"><button disabled={busy} onClick={() => act(`/duels/${duel.id}/scores/${latest.id}/confirm`)}>Confirm score</button>
      <form onSubmit={event => submit(event, `/duels/${duel.id}/scores/${latest.id}/dispute`, { reason })}><label>Dispute with reason<input minLength={10} maxLength={1000} value={reason} onChange={event => setReason(event.target.value)} placeholder="Explain what is wrong" required /></label><button className="secondary" disabled={busy}>Dispute</button></form></div>}
    {canScore && <details><summary>{latest ? 'Correct or reaffirm score' : 'Enter final score'}</summary><form className="form-grid score-form" onSubmit={event => submit(event, `/duels/${duel.id}/scores`, { score_a: Number(scoreA), score_b: Number(scoreB), source_url: source })}>
      <p className="full muted">Wait until FPL finalizes this gameweek, including postponed fixtures. Enter official captain slot points for captain duels.</p>
      <label>{a} points<input type="number" min="0" value={scoreA} onChange={event => setScoreA(event.target.value)} required /></label><label>{b} points<input type="number" min="0" value={scoreB} onChange={event => setScoreB(event.target.value)} required /></label>
      <label className="full">Official FPL source URL<input type="url" value={source} onChange={event => setSource(event.target.value)} placeholder="https://fantasy.premierleague.com/..." required /></label><button disabled={busy}>Post score &amp; email players</button></form></details>}
    {admin && duel.status === 'open' && <details><summary>Wrong deadline?</summary><form className="inline-form" onSubmit={event => submit(event, `/duels/${duel.id}/void`, { reason: voidReason })}><label>Reason<input minLength={5} value={voidReason} onChange={event => setVoidReason(event.target.value)} required /></label><button className="secondary" disabled={busy}>Void duel</button></form></details>}
    {admin && onRematch && ['resolved', 'void'].includes(duel.status) && <div className="rematch">
      <button type="button" className="secondary" aria-expanded={rematchOpen} onClick={() => setRematchOpen(!rematchOpen)} disabled={busy}>
        {rematchOpen ? 'Cancel rematch' : 'Set up rematch'}
      </button>
      {rematchOpen && <CreateDuelForm members={members} busy={busy}
        rematch={{ member_a_id: duel.member_a_id, member_b_id: duel.member_b_id, claim_type: duel.claim_type }}
        onCreate={async body => { if (await onRematch(body)) setRematchOpen(false) }} />}
    </div>}
  </article>
}
