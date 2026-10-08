import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import type { Session } from '@supabase/auth-js'
import { api, auth } from './client'
import type { Duel, Group, MemberHistory, Person } from './client'
import { CreateDuelForm, DuelCard } from './DuelCard'
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
  const group = groups.find(item => item.id === selected)

  useEffect(() => {
    auth.getSession().then(({ data }) => setSession(data.session))
    const { data } = auth.onAuthStateChange((_event, next) => setSession(next))
    return () => data.subscription.unsubscribe()
  }, [])

  const refresh = useCallback(async (groupId?: string) => {
    const profile = await api<Person>('/me')
    const groupList = await api<Group[]>('/groups')
    setMe(profile); setGroups(groupList); setUsername(profile.username || '')
    const id = groupId || selected || groupList[0]?.id
    if (id && groupList.some(g => g.id === id)) {
      setSelected(id)
      const [people, duelList, records] = await Promise.all([
        api<Person[]>(`/groups/${id}/members`), api<Duel[]>(`/groups/${id}/duels`),
        api<Record<string, MemberHistory>>(`/groups/${id}/history`),
      ])
      setMembers(people); setDuels(duelList); setHistory(records)
    } else { setSelected(''); setMembers([]); setDuels([]); setHistory({}) }
    setError('')
  }, [selected])

  useEffect(() => { if (session) refresh().catch(err => setError(String(err))) }, [session, refresh])

  async function run(action: () => Promise<unknown>, groupId?: string) {
    setError(''); setBusy(true)
    try { const result = await action(); await refresh(groupId || (result as { id?: string } | undefined)?.id) }
    catch (err) { setError(err instanceof Error ? err.message : String(err)) }
    finally { setBusy(false) }
  }

  async function signIn(event: FormEvent) {
    event.preventDefault(); setError('')
    const { error: authError } = await auth.signInWithOtp({ email, options: { emailRedirectTo: window.location.origin } })
    if (authError) setError(authError.message)
    else setSent(true)
  }

  if (!session) return <main className="shell auth-page"><div className="brand">RIVALRY <span>COURT</span></div>
    <section className="panel"><p className="eyebrow">FPL WITH RECEIPTS</p><h1>Settle the argument after the gameweek.</h1>
      <p>Lock a prediction against a friend before the deadline. Revisit it when the scores are final.</p>
      <form onSubmit={signIn}><label>Email address<input type="email" value={email} onChange={event => setEmail(event.target.value)} required placeholder="you@example.com" /></label>
        <button type="submit">Send sign-in link</button></form>
      {sent && <p className="success">Check your email. In local development, open Mailpit at <a href="http://localhost:8025" target="_blank">localhost:8025</a>.</p>}
      {error && <p className="error" role="alert">{error}</p>}</section></main>

  return <main className="shell">
    <header><div className="brand">RIVALRY <span>COURT</span></div><div className="account"><span>{me?.display_name}</span><button className="text-button" onClick={() => auth.signOut()}>Sign out</button></div></header>
    {error && <div className="error" role="alert">{error} <button className="secondary" onClick={() => refresh().catch(err => setError(String(err)))}>Try again</button></div>}
    <section className="panel profile-panel"><div><p className="eyebrow">YOUR NAME IN COURT</p><p>{me?.username ? 'Friends see this username on duels and records.' : 'Pick a username so friends see your name instead of a player number.'}</p></div>
      <form onSubmit={event => { event.preventDefault(); run(() => api('/me', 'PATCH', { username })) }}>
        <label>Username<input value={username} onChange={event => setUsername(event.target.value)} minLength={3} maxLength={24} pattern="[A-Za-z0-9_]+" autoComplete="nickname" placeholder="your_name" required /></label>
        <button disabled={busy || username.toLowerCase() === me?.username}>Save</button>
      </form></section>
    <section className="panel group-panel"><div><p className="eyebrow">YOUR COURT</p><h1>Make the call before kickoff.</h1></div>
      <div className="group-controls"><label>Group<select value={selected} onChange={event => { setSelected(event.target.value); refresh(event.target.value).catch(err => setError(String(err))) }}>
        {groups.length === 0 && <option value="">No group yet</option>}
        {groups.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
        <form onSubmit={event => { event.preventDefault(); run(async () => { const made = await api<Group>('/groups', 'POST', { name: groupName }); setNewCode({ groupId: made.id, code: made.invite_code || '' }); setGroupName(''); return made }) }}>
          <label>Create a group<input value={groupName} onChange={event => setGroupName(event.target.value)} placeholder="Weekend rivals" required minLength={2} /></label><button disabled={busy}>Create</button></form>
        <form onSubmit={event => { event.preventDefault(); run(async () => { const joined = await api<Group>('/groups/join', 'POST', { invite_code: inviteCode }); setInviteCode(''); return joined }) }}>
          <label>Join by invite code<input value={inviteCode} onChange={event => setInviteCode(event.target.value)} placeholder="Paste invite code" required /></label><button disabled={busy}>Join</button></form>
        {group?.role === 'admin' && <div className="invite-actions"><button className="secondary" disabled={busy} onClick={() => run(async () => {
          const rotated = await api<Group>(`/groups/${group.id}/invite-code`, 'POST')
          setNewCode({ groupId: group.id, code: rotated.invite_code || '' })
        }, group.id)}>Generate new invite code</button><small>This replaces the previous code.</small></div>}
      </div>{newCode?.groupId === selected && <p className="success">Share this invite code with friends: <strong>{newCode.code}</strong> (shown once)</p>}</section>

    {group && <>
      <section className="section-heading"><div><p className="eyebrow">{group.name.toUpperCase()}</p><h2>Duels</h2></div><button className="secondary" onClick={() => refresh().catch(err => setError(String(err)))}>Refresh</button></section>
      {group.role === 'admin' && <CreateDuelForm members={members} busy={busy} onCreate={body => run(() => api(`/groups/${group.id}/duels`, 'POST', body))} />}
      {duels.length === 0 && <div className="panel empty">No duels yet. Invite a friend, then create one.</div>}
      <div className="duel-grid">{duels.map(duel => <DuelCard key={duel.id} duel={duel} me={me!} members={members} admin={group.role === 'admin'} busy={busy} act={(path, body) => run(() => api(path, 'POST', body))} />)}</div>
      <section className="section-heading"><div><p className="eyebrow">THE RECORD</p><h2>History &amp; calibration</h2></div></section>
      <div className="stats-grid">{Object.entries(history).map(([id, record]) => <div className="panel stat" key={id}>
        <h3>{record.display_name}{id === me?.id && <small> You</small>}</h3><div className="stat-row"><strong>{record.wins}–{record.losses}</strong><span>W–L</span></div>
        <div className="stat-row"><strong>{record.sample_size}</strong><span>Resolved predictions</span></div>
        <div className="stat-row"><strong>{record.mean_brier === null ? '—' : record.mean_brier.toFixed(3)}</strong><span>Mean Brier · lower is better</span></div>
        {record.history.length > 0 && <details><summary>Activity ({record.history.length})</summary><ul>{record.history.map(item => <li key={item.duel_id}>{item.gameweek} · {item.status === 'void' ? `Void: ${item.void_reason}` : `${item.won ? 'Won' : 'Lost'} · ${item.probability_pct}% · Brier ${item.brier?.toFixed(3)}`}</li>)}</ul></details>}
      </div>)}</div>
    </>}
  </main>
}
