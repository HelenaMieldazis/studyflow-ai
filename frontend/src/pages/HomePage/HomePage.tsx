import { HealthStatus } from '../../components/HealthStatus/HealthStatus'
import { useHealthCheck } from '../../hooks/useHealthCheck'
import styles from './HomePage.module.css'

/** Página inicial da Etapa 1: confirma a comunicação frontend ↔ backend ↔ banco. */
export function HomePage() {
  const { state, retry } = useHealthCheck()

  return (
    <>
      <h1 className={styles.title}>Bem-vindo ao StudyFlow AI</h1>
      <p className={styles.lead}>
        Plataforma de organização de estudos com tutor de IA adaptativo. Esta é a fundação do projeto.
      </p>
      <HealthStatus state={state} onRetry={retry} />
    </>
  )
}
