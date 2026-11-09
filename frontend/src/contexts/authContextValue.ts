import { createContext } from 'react'
import type { LoginInput, RegisterInput, SessionResponse, User } from '../types/auth'

export type AuthStatus = 'loading' | 'authenticated' | 'anonymous'

/** Aviso exibido na tela de login depois que a sessão termina sem ser por "Sair". */
export type AuthNotice = 'session_expired' | 'account_deleted' | 'logged_out'

export type AuthContextValue = {
  status: AuthStatus
  user: User | null
  /** Motivo do fim da sessão, para a tela de login avisar (null quando não há aviso). */
  notice: AuthNotice | null
  login: (input: LoginInput) => Promise<void>
  register: (input: RegisterInput) => Promise<void>
  logout: () => Promise<void>
  /** Atualiza os dados do usuário em memória (após editar o perfil). */
  setUser: (user: User) => void
  /** Aplica uma nova sessão (após trocar a senha, o backend emite um novo token CSRF). */
  applySession: (session: SessionResponse) => void
  /** Limpa o estado local (ex.: após excluir a conta), opcionalmente com um aviso. */
  clearSession: (notice?: AuthNotice) => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)
