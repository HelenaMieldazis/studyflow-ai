import { act, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as api from './services/api'
import * as authService from './services/authService'
import { fetchConnectionState } from './services/healthService'
import { ANA, UNAUTHENTICATED, renderApp, session } from './test/utils'

vi.mock('./services/authService')
vi.mock('./services/healthService', () => ({
  fetchConnectionState: vi.fn(async () => ({ kind: 'offline' })),
}))

const mocked = vi.mocked(authService)

beforeEach(() => {
  vi.mocked(fetchConnectionState).mockResolvedValue({ kind: 'offline' })
})

describe('rotas e autenticação', () => {
  it('redireciona visitantes não autenticados para a tela de login', async () => {
    mocked.fetchCurrentSession.mockRejectedValue(UNAUTHENTICATED())
    renderApp('/configuracoes')

    expect(await screen.findByRole('heading', { name: 'Entrar' })).toBeInTheDocument()
  })

  it('mostra a visão geral e o menu para quem está autenticado', async () => {
    mocked.fetchCurrentSession.mockResolvedValue(session())
    renderApp('/')

    expect(await screen.findByRole('heading', { level: 1, name: 'Olá, Ana' })).toBeInTheDocument()
    const nav = screen.getByRole('navigation', { name: 'Menu principal' })
    expect(within(nav).getByRole('link', { name: 'Visão geral' })).toHaveAttribute('aria-current', 'page')
    expect(within(nav).getByRole('link', { name: 'Configurações' })).toBeInTheDocument()
  })

  it('leva quem já está autenticado da tela de login para o painel', async () => {
    mocked.fetchCurrentSession.mockResolvedValue(session())
    renderApp('/entrar')

    expect(await screen.findByRole('heading', { name: 'Olá, Ana' })).toBeInTheDocument()
  })

  it('a página de privacidade é pública', async () => {
    mocked.fetchCurrentSession.mockRejectedValue(UNAUTHENTICATED())
    renderApp('/privacidade')

    expect(await screen.findByRole('heading', { name: 'Como usamos seus dados' })).toBeInTheDocument()
  })

  it('exibe 404 para rotas desconhecidas (usuário autenticado)', async () => {
    mocked.fetchCurrentSession.mockResolvedValue(session())
    renderApp('/rota-inexistente')

    expect(await screen.findByRole('heading', { name: 'Página não encontrada' })).toBeInTheDocument()
  })

  it('sair encerra a sessão e volta para o login', async () => {
    mocked.fetchCurrentSession.mockResolvedValue(session())
    mocked.logout.mockResolvedValue()
    const user = userEvent.setup()
    renderApp('/')

    await user.click(await screen.findByRole('button', { name: 'Sair' }))

    expect(mocked.logout).toHaveBeenCalledOnce()
    expect(await screen.findByRole('heading', { name: 'Entrar' })).toBeInTheDocument()
    expect(screen.getByText('Você saiu da sua conta.')).toBeInTheDocument()
  })

  it('após sair numa página interna, o próximo login abre o painel (não a página anterior)', async () => {
    mocked.fetchCurrentSession.mockResolvedValue(session())
    mocked.logout.mockResolvedValue()
    mocked.login.mockResolvedValue(session())
    const user = userEvent.setup()
    renderApp('/configuracoes')

    await user.click(await screen.findByRole('button', { name: 'Sair' }))
    await user.type(await screen.findByLabelText('E-mail'), 'ana@example.com')
    await user.type(screen.getByLabelText('Senha'), 'uma-senha-bem-longa-123')
    await user.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(await screen.findByRole('heading', { name: 'Olá, Ana' })).toBeInTheDocument()
  })

  it('quando a sessão expira durante o uso, volta ao login com aviso', async () => {
    let onExpired: (() => void) | null = null
    vi.spyOn(api, 'setUnauthenticatedHandler').mockImplementation((handler) => {
      if (handler) onExpired = handler
    })
    mocked.fetchCurrentSession.mockResolvedValue(session())
    renderApp('/configuracoes')
    await screen.findByRole('heading', { name: 'Configurações' })

    act(() => onExpired?.())

    expect(await screen.findByText('Sua sessão expirou. Entre novamente.')).toBeInTheDocument()
  })

  it('exibe nomes com HTML como texto, sem executar nada (XSS)', async () => {
    const payload = '<img src=x onerror="window.__xss=1"><script>window.__xss=1</script>'
    mocked.fetchCurrentSession.mockResolvedValue(session({ ...ANA, display_name: payload }))
    const { container } = renderApp('/')

    expect(await screen.findByRole('heading', { level: 1 })).toHaveTextContent(`Olá, ${payload}`)
    expect(container.querySelector('img')).toBeNull()
    expect(container.querySelector('script')).toBeNull()
    expect((window as unknown as { __xss?: number }).__xss).toBeUndefined()
  })

  it('oferece link para pular direto ao conteúdo (acessibilidade)', async () => {
    mocked.fetchCurrentSession.mockResolvedValue(session())
    renderApp('/')

    expect(await screen.findByRole('link', { name: 'Pular para o conteúdo' })).toHaveAttribute('href', '#conteudo')
    expect(screen.getByRole('main')).toHaveAttribute('id', 'conteudo')
  })
})
