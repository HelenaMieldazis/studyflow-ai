import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import * as authService from '../../services/authService'
import { UNAUTHENTICATED, apiError, renderApp, session } from '../../test/utils'

vi.mock('../../services/authService')
vi.mock('../../services/healthService', () => ({ fetchConnectionState: vi.fn(async () => ({ kind: 'offline' })) }))

const mocked = vi.mocked(authService)

async function openLogin(state?: unknown) {
  mocked.fetchCurrentSession.mockRejectedValue(UNAUTHENTICATED())
  renderApp('/entrar', state)
  await screen.findByRole('heading', { name: 'Entrar' })
  return userEvent.setup()
}

describe('LoginPage', () => {
  it('valida os campos antes de enviar', async () => {
    const user = await openLogin()

    await user.type(screen.getByLabelText('E-mail'), 'nao-e-email')
    await user.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(screen.getByText('Informe um e-mail válido.')).toBeInTheDocument()
    expect(screen.getByText('Informe sua senha.')).toBeInTheDocument()
    expect(screen.getByLabelText('E-mail')).toHaveAttribute('aria-invalid', 'true')
    expect(mocked.login).not.toHaveBeenCalled()
  })

  it('mostra a mensagem genérica do servidor e limpa a senha em caso de erro', async () => {
    mocked.login.mockRejectedValue(apiError(401, { code: 'invalid_credentials', message: 'E-mail ou senha incorretos.' }))
    const user = await openLogin()

    await user.type(screen.getByLabelText('E-mail'), 'ana@example.com')
    await user.type(screen.getByLabelText('Senha'), 'senha-errada-123')
    await user.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('E-mail ou senha incorretos.')
    expect(screen.getByLabelText('Senha')).toHaveValue('')
  })

  it('mostra aviso de muitas tentativas (rate limiting)', async () => {
    mocked.login.mockRejectedValue(
      apiError(429, { code: 'too_many_requests', message: 'Muitas requisições. Tente novamente em instantes.' }),
    )
    const user = await openLogin()

    await user.type(screen.getByLabelText('E-mail'), 'ana@example.com')
    await user.type(screen.getByLabelText('Senha'), 'qualquer-senha-1')
    await user.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Muitas requisições')
  })

  it('após o login, volta para a página que a pessoa tentou abrir', async () => {
    mocked.login.mockResolvedValue(session())
    const user = await openLogin({ from: '/configuracoes' })

    await user.type(screen.getByLabelText('E-mail'), 'ana@example.com')
    await user.type(screen.getByLabelText('Senha'), 'uma-senha-bem-longa-123')
    await user.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(await screen.findByRole('heading', { name: 'Configurações' })).toBeInTheDocument()
    expect(mocked.login).toHaveBeenCalledWith({ email: 'ana@example.com', password: 'uma-senha-bem-longa-123' })
  })

  it('ignora destinos externos após o login (open redirect)', async () => {
    mocked.login.mockResolvedValue(session())
    const user = await openLogin({ from: '//site-malicioso.example' })

    await user.type(screen.getByLabelText('E-mail'), 'ana@example.com')
    await user.type(screen.getByLabelText('Senha'), 'uma-senha-bem-longa-123')
    await user.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(await screen.findByRole('heading', { name: 'Olá, Ana' })).toBeInTheDocument()
  })
})
