import { describe, expect, it } from 'vitest'
import { safeRedirectPath } from './redirect'

describe('safeRedirectPath', () => {
  it.each(['/', '/configuracoes', '/trilhas?id=1'])('aceita caminho interno %s', (path) => {
    expect(safeRedirectPath(path)).toBe(path)
  })

  it.each(['//evil.example', '/\\evil.example', 'https://evil.example', 'javascript:alert(1)', '', null, 42])(
    'bloqueia destino externo ou inválido %s (open redirect)',
    (value) => {
      expect(safeRedirectPath(value)).toBe('/')
    },
  )
})
