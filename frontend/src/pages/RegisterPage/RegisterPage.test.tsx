import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import * as authService from '../../services/authService'
import { UNAUTHENTICATED, apiError, renderApp, session } from '../../test/utils'

vi.mock('../../services/authService')
vi.mock('../../services/healthService', () => ({ fetchConnectionState: vi.fn(async () => ({ kind: 'offline' })) }))

const mocked = vi.mocked(authService)

async function openRegister() {
  mocked.fetchCurrentSession.mockRejectedValue(UNAUTHENTICATED())
  renderApp('/cadastro')
  await screen.findByRole('heading', { name: 'Criar conta' })
  return userEvent.setup()
}

async function fill(user: ReturnType<typeof userEvent.setup>, values: Record<string, string>) {
  for (const [label, value] of Object.entries(values)) {
    if (value) await user.type(screen.getByLabelText(label), value)
  }
}

describe('RegisterPage', () => {
  it('exige senha forte e confirmação igual', async () => {
    const user = await openRegister()
    await fill(user, { Nome: 'Ana', 'E-mail': 'ana@example.com', Senha: 'curta', 'Confirmar senha': 'outra' })
    await user.click(screen.getByRole('button', { name: 'Criar conta' }))

    expect(screen.getByText('Use pelo menos 12 caracteres.')).toBeInTheDocument()
    expect(screen.getByText('As senhas não conferem.')).toBeInTheDocument()
    expect(mocked.register).not.toHaveBeenCalled()
  })

  it('mostra o erro do servidor no campo de e-mail quando ele já está em uso', async () => {
    mocked.register.mockRejectedValue(
      apiError(409, { code: 'email_unavailable', message: 'Não foi possível usar este e-mail. Verifique-o ou faça login.' }),
    )
    const user = await openRegister()
    await fill(user, {
      Nome: 'Ana',
      'E-mail': 'ana@example.com',
      Senha: 'uma-senha-bem-longa-123',
      'Confirmar senha': 'uma-senha-bem-longa-123',
    })
    await user.click(screen.getByRole('button', { name: 'Criar conta' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Não foi possível usar este e-mail')
    expect(screen.getByLabelText('E-mail')).toHaveAttribute('aria-invalid', 'true')
  })

  it('cria a conta, inicia a sessão e abre o painel', async () => {
    mocked.register.mockResolvedValue(session())
    const user = await openRegister()
    await fill(user, {
      Nome: '  Ana  ',
      'E-mail': 'ana@example.com',
      Senha: 'uma-senha-bem-longa-123',
      'Confirmar senha': 'uma-senha-bem-longa-123',
    })
    await user.click(screen.getByRole('button', { name: 'Criar conta' }))

    expect(await screen.findByRole('heading', { name: 'Olá, Ana' })).toBeInTheDocument()
    expect(mocked.register).toHaveBeenCalledWith({
      display_name: 'Ana',
      email: 'ana@example.com',
      password: 'uma-senha-bem-longa-123',
    })
  })

  it('informa como os dados serão usados', async () => {
    await openRegister()
    expect(screen.getByRole('link', { name: 'Como usamos seus dados' })).toHaveAttribute('href', '/privacidade')
  })
})
