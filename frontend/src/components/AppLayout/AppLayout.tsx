import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { HomeIcon, LogoutIcon, SettingsIcon } from '../icons/Icons'
import styles from './AppLayout.module.css'

/**
 * Estrutura das páginas autenticadas: barra superior + menu lateral.
 * O menu mostra só o que já existe. "Meus estudos", "Trilhas", "Calendário",
 * "Biblioteca", "Tutor IA" e "Meu progresso" entram junto com cada funcionalidade.
 */
const NAV_ITEMS = [
  { to: '/', label: 'Visão geral', icon: <HomeIcon />, end: true },
  { to: '/configuracoes', label: 'Configurações', icon: <SettingsIcon />, end: false },
]

export function AppLayout() {
  const { user, logout } = useAuth()
  const [loggingOut, setLoggingOut] = useState(false)

  async function handleLogout() {
    setLoggingOut(true)
    // Sem sessão, o ProtectedRoute leva à tela de login.
    await logout()
  }

  return (
    <div className={styles.shell}>
      <a href="#conteudo" className={styles.skipLink}>
        Pular para o conteúdo
      </a>
      <header className={styles.topbar}>
        <span className={styles.brand}>
          StudyFlow <span className={styles.brandAccent}>AI</span>
        </span>
        <div className={styles.userArea}>
          {/* Texto puro: o React escapa o conteúdo, então um nome com HTML não é interpretado. */}
          <span className={styles.userName}>{user?.display_name}</span>
          <button type="button" className={styles.logout} onClick={handleLogout} disabled={loggingOut}>
            <LogoutIcon />
            <span>Sair</span>
          </button>
        </div>
      </header>

      <div className={styles.body}>
        <nav className={styles.sidebar} aria-label="Menu principal">
          <ul>
            {NAV_ITEMS.map((item) => (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  end={item.end}
                  className={({ isActive }) => `${styles.navLink} ${isActive ? styles.active : ''}`}
                >
                  {item.icon}
                  <span>{item.label}</span>
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        <main id="conteudo" className={styles.main} tabIndex={-1}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}
