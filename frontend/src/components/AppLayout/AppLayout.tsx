import { Outlet } from 'react-router-dom'
import styles from './AppLayout.module.css'

/**
 * Estrutura base das páginas.
 * O menu lateral completo (Visão geral, Meus estudos, Trilhas…) será adicionado
 * junto com as respectivas funcionalidades, a partir da Etapa 3.
 */
export function AppLayout() {
  return (
    <div className={styles.shell}>
      <a href="#conteudo" className={styles.skipLink}>
        Pular para o conteúdo
      </a>
      <header className={styles.topbar}>
        <span className={styles.brand}>
          StudyFlow <span className={styles.brandAccent}>AI</span>
        </span>
      </header>
      <main id="conteudo" className={styles.main} tabIndex={-1}>
        <Outlet />
      </main>
    </div>
  )
}
