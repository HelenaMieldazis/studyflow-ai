import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { safeRedirectPath } from '../../utils/redirect'
import { FullPageLoader } from '../FullPageLoader/FullPageLoader'

/**
 * Exibe as rotas filhas só para quem está autenticado.
 * Observação: isto é conveniência de interface. A proteção real está no backend,
 * que valida a sessão em toda rota privada.
 */
export function ProtectedRoute() {
  const { status, notice } = useAuth()
  const location = useLocation()

  if (status === 'loading') return <FullPageLoader />
  if (status === 'anonymous') {
    // Lembra a página só quando a pessoa não saiu por vontade própria (primeiro acesso
    // ou sessão expirada). Depois de "Sair" ou de excluir a conta, o próximo login abre o painel.
    const remember = notice === null || notice === 'session_expired'
    return (
      <Navigate to="/entrar" replace state={remember ? { from: location.pathname + location.search } : undefined} />
    )
  }
  return <Outlet />
}

/**
 * Telas de login/cadastro: quem está autenticado é levado à página que tentou abrir
 * antes do login (somente caminhos internos) ou ao painel.
 * É este guard que faz o redirecionamento pós-login, num único lugar.
 */
export function PublicOnlyRoute() {
  const { status } = useAuth()
  const location = useLocation()

  if (status === 'loading') return <FullPageLoader />
  if (status === 'authenticated') {
    const from = (location.state as { from?: unknown } | null)?.from
    return <Navigate to={safeRedirectPath(from)} replace />
  }
  return <Outlet />
}
