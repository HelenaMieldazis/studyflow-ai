import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import App from './App'
import { fetchConnectionState } from './services/healthService'

// Nenhum teste de interface faz chamada de rede real.
vi.mock('./services/healthService', () => ({
  fetchConnectionState: vi.fn(async () => ({ kind: 'offline' })),
}))

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
}

describe('App', () => {
  it('na página inicial consulta o backend e exibe o resultado', async () => {
    const spy = vi.mocked(fetchConnectionState).mockResolvedValue({
      kind: 'online',
      data: { status: 'ok', service: 'studyflow-api', checks: { database: 'ok' } },
    })

    renderAt('/')

    expect(screen.getByRole('heading', { level: 1, name: 'Bem-vindo ao StudyFlow AI' })).toBeInTheDocument()
    expect(await screen.findByText('Sistema operacional')).toBeInTheDocument()
    expect(spy).toHaveBeenCalled()
  })

  it('exibe página 404 para rotas desconhecidas', () => {
    renderAt('/rota-inexistente')

    expect(screen.getByRole('heading', { name: 'Página não encontrada' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Voltar para o início' })).toHaveAttribute('href', '/')
  })

  it('oferece link para pular direto ao conteúdo (acessibilidade)', () => {
    renderAt('/rota-inexistente')

    expect(screen.getByRole('link', { name: 'Pular para o conteúdo' })).toHaveAttribute('href', '#conteudo')
    expect(screen.getByRole('main')).toHaveAttribute('id', 'conteudo')
  })
})
