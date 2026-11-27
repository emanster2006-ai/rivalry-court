import { useCallback, useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import type { Session } from '@supabase/auth-js'
import { api, auth } from './client'
import type { Duel, Group, MemberHistory, Person } from './client'
import { CreateDuelForm, DuelCard, duelAction } from './DuelCard'
import type { CreateDuelInput } from './DuelCard'
import './style.css'

export default function App() {
  const [session, setSession] = useState<Session | null>(null)
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [sent, setSent] = useState(false)
  const [me, setMe] = useState<Person | null>(null)
  const [groups, setGroups] = useState<Group[]>([])
  const [selected, setSelected] = useState<string>('')
  const [members, setMembers] = useState<Person[]>([])
  const [duels, setDuels] = useState<Duel[]>([])
  const [history, setHistory] = useState<Record<string, MemberHistory>>({})
  const [newCode, setNewCode] = useState<{ groupId: string; code: string } | null>(null)
  const [groupName, setGroupName] = useState('')
  const [inviteCode, setInviteCode] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [linkedDuelId] = useState(() => new URLSearchParams(window.location.search).get('duel'))
  const [linkUnavailable, setLinkUnavailable] = useState(false)
  const refreshVersion = useRef(0)
  const group = groups.find(item => item.id === selected)

  useEffect(() => {
    auth.getSession().then(({ data }) => setSession(data.session))
    const { data } = auth.onAuthStateChange((_event, next) => setSession(next))
    return () => data.subscription.unsubscribe()
  }, [])

  const refresh = useCallback(async (groupId?: string) => {
    const version = ++refreshVersion.current
    const [profile, groupList] = await Promise.all([api<Person>('/me'), api<Group[]>('/groups')])
    let linkedGroupId: string | undefined
    if (linkedDuelId && !groupId) {
      try {
        const linkedDuel = await api<Duel>(`/duels/${encodeURIComponent(linkedDuelId)}`)
        linkedGroupId = groupList.find(item => item.id === linkedDuel.group_id)?.id
      } catch {
        // A stale or inaccessible link should still let the member open their groups.
      }
    }
    const id = groupId || linkedGroupId || groupList[0]?.id
    if (id && groupList.some(g => g.id === id)) {
      const [people, duelList, records] = await Promise.all([
        api<Person[]>(`/groups/${id}/members`), api<Duel[]>(`/groups/${id}/duels`),
        api<Record<string, MemberHistory>>(`/groups/${id}/history`),
      ])
      if (version !== refreshVersion.current) return
      setSelected(id)
      setMembers(people); setDuels(duelList); setHistory(records)
    } else {
      if (version !== refreshVersion.current) return
      setSelected(''); setMembers([]); setDuels([]); setHistory({})
    }
    setMe(profile); setGroups(groupList); setUsername(profile.username || '')
    if (!groupId) setLinkUnavailable(Boolean(linkedDuelId && !linkedGroupId))
    setError('')
  }, [linkedDuelId])

  const signedIn = Boolean(session)
  useEffect(() => {
    if (signedIn) refresh().catch(err => setError(String(err)))
    else {
      setMe(null); setGroups([]); setSelected(''); setMembers([]); setDuels([]); setHistory({})
      setNewCode(null); setLinkUnavailable(false)
    }
    return () => { refreshVersion.current += 1 }
  }, [signedIn, refresh])

  useEffect(() => {
    if (!signedIn || !selected || busy) return
    const now = Date.now()
    const deadline = Math.min(...duels.filter(duel => duel.status === 'open')
      .map(duel => Date.parse(duel.deadline_at))
      .filter(value => value > now))
    if (!Number.isFinite(deadline)) return
    const version = refreshVersion.current
    const timer = window.setTimeout(() => {
      if (version === refreshVersion.current) refresh(selected).catch(err => setError(String(err)))
    }, Math.min(deadline - now + 250, 2_147_483_647))
    return () => window.clearTimeout(timer)
  }, [busy, duels, refresh, selected, signedIn])

  async function run(action: () => Promise<unknown>, selectReturnedGroup = false) {
    setError(''); setBusy(true)
    let saved = false
    try {
      const result = await action()
      saved = true
      await refresh(selectReturnedGroup ? (result as Group).id : selected)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    }
    finally { setBusy(false) }
    return saved
  }

  function createDuel(body: CreateDuelInput) {
    return run(() => api(`/groups/${selected}/duels`, 'POST', body))
  }

  async function signIn(event: FormEvent) {
    event.preventDefault(); setError('')
    const redirect = linkedDuelId
      ? `${window.location.origin}/?duel=${encodeURIComponent(linkedDuelId)}`
      : window.location.origin
    const { error: authError } = await auth.signInWithOtp({ email, options: { emailRedirectTo: redirect } })
    if (authError) setError(authError.message)
    else setSent(true)
  }

  if (!session) return <main className="shell auth-page"><div className="brand">RIVALRY <span>COURT</span></div>
    <section className="panel"><p className="eyebrow">FPL WITH RECEIPTS</p><h1>Settle the argument after the gameweek.</h1>
      <p>Lock a prediction against a friend before the deadline. Revisit it when the scores are final.</p>
      <form onSubmit={signIn}><label>Email address<input type="email" value={email} onChange={event => setEmail(event.target.value)} required placeholder="you@example.com" /></label>
        <button type="submit">Send sign-in link</button></form>
      {sent && <p className="success">Check your email for the sign-in link (look in spam too).
        {import.meta.env.DEV && <> In local development, open Mailpit at <a href="http://localhost:8025" target="_blank">localhost:8025</a>.</>}</p>}
      {error && <p className="error" role="alert">{error}</p>}</section></main>

  const admin = group?.role === 'admin'
  const now = Date.now()
  const actionable = me
    ? duels.map(duel => ({ duel, action: duelAction(duel, me.id, admin, now) }))
    : []
  const featured = duels.find(duel => duel.id === linkedDuelId)
    ?? actionable.filter(item => item.action === 'predict')
      .sort((a, b) => Date.parse(a.duel.deadline_at) - Date.parse(b.duel.deadline_at))[0]?.duel
    ?? actionable.find(item => item.action === 'review')?.duel
    ?? actionable.find(item => item.action === 'score')?.duel
    ?? actionable.find(item => item.action === 'saved')?.duel
  const orderedDuels = featured ? [featured, ...duels.filter(duel => duel.id !== featured.id)] : duels

  return <main className="shell">
    <header><div className="brand">RIVALRY <span>COURT</span></div><div className="account"><span>{me?.display_name}</span><button className="text-button" onClick={() => auth.signOut()}>Sign out</button></div></header>
    {!me && !error && <p className="muted" role="status">Loading your court…</p>}
    {error && <div className="error" role="alert">{error} <button className="secondary" onClick={() => refresh(selected || undefined).catch(err => setError(String(err)))}>Try again</button></div>}
    {linkUnavailable && <p className="error" role="status">Couldn’t open the linked duel. Check that you’re signed in with the account that joined its group.</p>}
    {me && !me.username && <section className="panel profile-panel"><div><h2>Choose a username</h2>
      <p>Friends see this on duels and records. <strong>You can only choose it once.</strong></p></div>
      <form onSubmit={event => { event.preventDefault(); run(() => api('/me', 'PATCH', { username })) }}>
        <label>Username<input value={username} onChange={event => setUsername(event.target.value)} minLength={3} maxLength={24} pattern="[A-Za-z0-9_]+" autoComplete="nickname" placeholder="your_name" required /></label>
        <button disabled={busy}>Save permanently</button>
      </form></section>}

    {group && me && <>
      <section aria-labelledby="duels-heading">
        <div className="dashboard-heading">
          <h1 id="duels-heading">{group.name}</h1>
          <div className="dashboard-controls">
            {groups.length > 1 && <select aria-label="Group" value={selected} disabled={busy} onChange={event => refresh(event.target.value).catch(err => setError(String(err)))}>
              {groups.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>}
            <button className="secondary" disabled={busy} onClick={() => refresh(selected).catch(err => setError(String(err)))}>Refresh duels</button>
          </div>
        </div>
        {duels.length === 0 && <p className="panel empty">No duels yet. Invite a friend, then create one.</p>}
        <div className="duel-grid">{orderedDuels.map(duel => <DuelCard key={duel.id} duel={duel} me={me} members={members}
          admin={admin} busy={busy} featured={featured?.id === duel.id} onRematch={createDuel}
          act={(path, body) => run(() => api(path, 'POST', body))} />)}</div>
        {admin && <div className="new-duel"><CreateDuelForm key={group.id} members={members} busy={busy} onCreate={createDuel} /></div>}
      </section>
      <section className="section-heading"><h2>History &amp; calibration</h2></section>
      <div className="stats-grid">{Object.entries(history).map(([id, record]) => <div className="panel stat" key={id}>
        <h3>{record.display_name}{id === me.id && <small> You</small>}</h3><div className="stat-row"><strong>{record.wins}–{record.losses}</strong><span>W–L</span></div>
        <div className="stat-row"><strong>{record.sample_size}</strong><span>Resolved predictions</span></div>
        <div className="stat-row"><strong>{record.mean_brier === null ? '—' : record.mean_brier.toFixed(3)}</strong><span>Mean Brier · lower is better</span></div>
        {record.history.length > 0 && <details><summary>Activity ({record.history.length})</summary><ul>{record.history.map(item => <li key={item.duel_id}>{item.gameweek} · {item.status === 'void' ? `Void: ${item.void_reason}` : `${item.won ? 'Won' : 'Lost'} · ${item.probability_pct}% · Brier ${item.brier?.toFixed(3)}`}</li>)}</ul></details>}
      </div>)}</div>
    </>}

    {me && <details className="panel group-settings" open={!group || newCode?.groupId === selected}>
      <summary>Group settings</summary>
      <div className="group-controls">
        <form onSubmit={event => { event.preventDefault(); run(async () => { const made = await api<Group>('/groups', 'POST', { name: groupName }); setNewCode({ groupId: made.id, code: made.invite_code || '' }); setGroupName(''); return made }, true) }}>
          <label>Create a group<input value={groupName} onChange={event => setGroupName(event.target.value)} placeholder="Weekend rivals" required minLength={2} /></label><button disabled={busy}>Create</button></form>
        <form onSubmit={event => { event.preventDefault(); run(async () => { const joined = await api<Group>('/groups/join', 'POST', { invite_code: inviteCode }); setInviteCode(''); return joined }, true) }}>
          <label>Join by invite code<input value={inviteCode} onChange={event => setInviteCode(event.target.value)} placeholder="Paste invite code" required /></label><button disabled={busy}>Join</button></form>
        {group?.role === 'admin' && <div className="invite-actions"><button className="secondary" disabled={busy} onClick={() => run(async () => {
          const rotated = await api<Group>(`/groups/${group.id}/invite-code`, 'POST')
          setNewCode({ groupId: group.id, code: rotated.invite_code || '' })
        })}>Generate new invite code</button><small>This replaces the previous code.</small></div>}
      </div>
      {newCode?.groupId === selected && <p className="success">Share this invite code with friends: <strong>{newCode.code}</strong> (shown once)</p>}
    </details>}
  </main>
}
