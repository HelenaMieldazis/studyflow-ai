import { Outlet } from 'react-router-dom'
import styles from './AuthLayout.module.css'

/** Layout das telas públicas (entrar, cadastro): cartão centralizado. */
export function AuthLayout() {
  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <p className={styles.brand}>
          StudyFlow <span className={styles.brandAccent}>AI</span>
        </p>
        <div className={styles.card}>
          <Outlet />
        </div>
      </main>
    </div>
  )
}
