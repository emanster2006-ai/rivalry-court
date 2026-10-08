import { render, screen } from '@testing-library/react'
import { expect, test, vi } from 'vitest'
import { ErrorBoundary } from './ErrorBoundary'

function Broken(): never { throw new Error('boom') }

test('a rendering crash shows a recovery screen instead of a blank page', () => {
  vi.spyOn(console, 'error').mockImplementation(() => {})
  render(<ErrorBoundary><Broken /></ErrorBoundary>)
  expect(screen.getByText('Something went wrong.')).toBeTruthy()
  expect(screen.getByText('Reload')).toBeTruthy()
})
