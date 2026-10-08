import { Component } from 'react'
import type { ReactNode } from 'react'

export class ErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false }

  static getDerivedStateFromError() { return { failed: true } }

  render() {
    if (!this.state.failed) return this.props.children
    return <main className="shell"><section className="panel"><h1>Something went wrong.</h1>
      <p>The page hit an unexpected problem. Your predictions are saved on the server.</p>
      <button onClick={() => window.location.reload()}>Reload</button></section></main>
  }
}
