import { render, screen } from '@testing-library/react'
import { test, expect } from 'vitest'

test('placeholder renders', () => {
  render(<h1>Rivalry Court</h1>)
  expect(screen.getByText('Rivalry Court')).toBeTruthy()
})
