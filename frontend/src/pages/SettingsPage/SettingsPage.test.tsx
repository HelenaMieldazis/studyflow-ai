import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import * as authService from '../../services/authService'
import { ANA, UNAUTHENTICATED, apiError, renderApp, session } from '../../test/utils'

vi.mock('../../services/authService')
vi.mock('../../services/healthService', () => ({ fetchConnectionState: vi.fn(async () => ({ kind: 'offline' })) }))

const mocked = vi.mocked(authService)

async function openSettings() {
  mocked.fetchCurrentSession.mockResolvedValue(session())
  renderApp('/configuracoes')
  await screen.findByRole('heading', { name: 'Configurações' })
  return userEvent.setup()
}

const section = (name: string) => screen.getByRole('region', { name })

describe('SettingsPage', () => {
  it('atualiza o nome e reflete no cabeçalho', async () => {
    mocked.updateProfile.mockResolvedValue({ ...ANA, display_name: 'Ana Lima' })
    const user = await openSettings()
    const profile = section('Perfil')

    const name = within(profile).getByLabelText('Nome')
    await user.clear(name)
    await user.type(name, 'Ana Lima')
    await user.click(within(profile).getByRole('button', { name: 'Salvar perfil' }))

    expect(await within(profile).findByText('Perfil atualizado.')).toBeInTheDocument()
    expect(mocked.updateProfile).toHaveBeenCalledWith({ display_name: 'Ana Lima' })
    expect(screen.getByRole('banner')).toHaveTextContent('Ana Lima')
  })

  it('pede a senha atual somente quando o e-mail muda', async () => {
    const user = await openSettings()
    const profile = section('Perfil')
    expect(within(profile).queryByLabelText('Senha atual')).toBeNull()

    const email = within(profile).getByLabelText('E-mail')
    await user.clear(email)
    await user.type(email, 'nova@example.com')
    await user.click(within(profile).getByRole('button', { name: 'Salvar perfil' }))

    expect(within(profile).getByText('Informe sua senha atual para alterar o e-mail.')).toBeInTheDocument()
    expect(mocked.updateProfile).not.toHaveBeenCalled()
  })

  it('troca a senha e aplica a nova sessão', async () => {
    mocked.changePassword.mockResolvedValue(session(ANA, 'csrf-novo'))
    const user = await openSettings()
    const pw = section('Alterar senha')

    await user.type(within(pw).getByLabelText('Senha atual'), 'uma-senha-bem-longa-123')
    await user.type(within(pw).getByLabelText('Nova senha'), 'outra-senha-bem-longa-456')
    await user.type(within(pw).getByLabelText('Confirmar nova senha'), 'outra-senha-bem-longa-456')
    await user.click(within(pw).getByRole('button', { name: 'Alterar senha' }))

    expect(await within(pw).findByText(/Senha alterada/)).toBeInTheDocument()
    expect(within(pw).getByLabelText('Senha atual')).toHaveValue('')
  })

  it('mostra erro quando a senha atual está incorreta', async () => {
    mocked.changePassword.mockRejectedValue(apiError(403, { code: 'invalid_password', message: 'Senha atual incorreta.' }))
    const user = await openSettings()
    const pw = section('Alterar senha')

    await user.type(within(pw).getByLabelText('Senha atual'), 'senha-errada-0000')
    await user.type(within(pw).getByLabelText('Nova senha'), 'outra-senha-bem-longa-456')
    await user.type(within(pw).getByLabelText('Confirmar nova senha'), 'outra-senha-bem-longa-456')
    await user.click(within(pw).getByRole('button', { name: 'Alterar senha' }))

    expect(await within(pw).findByRole('alert')).toHaveTextContent('Senha atual incorreta.')
  })

  it('só permite excluir a conta após confirmação explícita e senha', async () => {
    mocked.deleteAccount.mockResolvedValue()
    // Depois da exclusão, a sessão não existe mais.
    const user = await openSettings()
    mocked.fetchCurrentSession.mockRejectedValue(UNAUTHENTICATED())
    const danger = section('Excluir conta')
    const button = within(danger).getByRole('button', { name: 'Excluir minha conta' })

    expect(button).toBeDisabled()
    await user.click(within(danger).getByLabelText('Entendo que esta ação é permanente.'))
    await user.type(within(danger).getByLabelText('Senha'), 'uma-senha-bem-longa-123')
    await user.click(button)

    expect(mocked.deleteAccount).toHaveBeenCalledWith('uma-senha-bem-longa-123')
    expect(await screen.findByText('Sua conta foi excluída.')).toBeInTheDocument()
  })
})
