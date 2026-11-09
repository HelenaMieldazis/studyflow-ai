import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { HealthStatus } from './HealthStatus'

const okData = { status: 'ok', service: 'studyflow-api', checks: { database: 'ok' } } as const

describe('HealthStatus', () => {
  it('mostra estado de carregamento e desabilita o botão', () => {
    render(<HealthStatus state={{ kind: 'loading' }} onRetry={() => {}} />)

    expect(screen.getByRole('status')).toHaveTextContent('Verificando conexão')
    expect(screen.getByRole('button', { name: 'Verificar novamente' })).toBeDisabled()
  })

  it('mostra sistema operacional com banco conectado', () => {
    render(<HealthStatus state={{ kind: 'online', data: okData }} onRetry={() => {}} />)

    expect(screen.getByRole('status')).toHaveTextContent('Sistema operacional')
    expect(screen.getByText('conectado')).toBeInTheDocument()
  })

  it('mostra banco indisponível no estado degradado', () => {
    render(
      <HealthStatus
        state={{ kind: 'degraded', data: { ...okData, status: 'degraded', checks: { database: 'unavailable' } } }}
        onRetry={() => {}}
      />,
    )

    expect(screen.getByRole('status')).toHaveTextContent('Banco de dados indisponível')
    expect(screen.getByText('indisponível')).toBeInTheDocument()
  })

  it('mostra servidor inacessível e permite tentar novamente pelo teclado', async () => {
    const onRetry = vi.fn()
    const user = userEvent.setup()
    render(<HealthStatus state={{ kind: 'offline' }} onRetry={onRetry} />)

    expect(screen.getByRole('status')).toHaveTextContent('Servidor inacessível')
    await user.tab()
    expect(screen.getByRole('button', { name: 'Verificar novamente' })).toHaveFocus()
    await user.keyboard('{Enter}')
    expect(onRetry).toHaveBeenCalledOnce()
  })
})
